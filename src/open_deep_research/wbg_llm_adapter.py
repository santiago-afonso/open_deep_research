"""WBG LLM Adapter for private API endpoints."""

import httpx
import json
import time
from typing import Any, Dict, List, Optional, Iterator
from pydantic import Field

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk

from .logging_config import logger
from .wbg_auth_manager import WBGAuthManager


class WBGAPIError(Exception):
    """Custom exception for WBG private API."""
    pass


class WBGChatModel(SimpleChatModel):
    """LangChain-compatible chat model for WBG's private API."""
    
    # Configuration Fields
    api_url: str = Field(..., description="The full API endpoint URL.")
    
    # Common parameters
    max_tokens: Optional[int] = Field(default=None)
    
    # gpt-4.1 specific
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)

    # o4-mini specific
    reasoning_effort: Optional[str] = Field(default=None)
    
    # Internal components
    auth_manager: Optional[WBGAuthManager] = Field(default=None, exclude=True)
    http_client: httpx.Client = Field(default_factory=httpx.Client, exclude=True)

    @property
    def _llm_type(self) -> str:
        return "wbg_private_api_chat_model"

    def _convert_messages_to_api_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Converts LangChain messages to the simple list of dicts the API expects."""
        api_messages = []
        for msg in messages:
            role = ""
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                raise ValueError(f"Unknown message type: {type(msg)}")
            api_messages.append({"role": role, "content": msg.content})
        return api_messages

    def _call(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """Synchronous call method."""
        logger.info("=== WBG LLM API Request Starting ===")
        start_time = time.time()
        
        # Extract model name from URL
        model_name = "o4-mini" if "o4-mini" in self.api_url else "gpt-4.1"
        logger.info(f"Model: {model_name}")
        logger.info(f"Number of messages: {len(messages)}")
        
        # Log message details
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            msg_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            logger.info(f"Message {i+1} ({msg_type}): {msg_preview}")
        
        # Get a valid Bearer Token
        try:
            logger.debug("Obtaining authentication token...")
            if not self.auth_manager:
                # Create a default WBGAuthManager if none provided
                self.auth_manager = WBGAuthManager()
                logger.debug("Created default WBGAuthManager")
            bearer_token = self.auth_manager.get_bearer_token()
            logger.debug("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            logger.exception("Full authentication error:")
            raise WBGAPIError(f"Authentication failed: {e}") from e

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {bearer_token[:10]}...{bearer_token[-10:]}",  # Log partial token for security
            "Content-Type": "application/json",
        }
        logger.debug(f"Request headers prepared (token partially hidden)")

        # Prepare payload with model-specific parameters
        payload = {
            "messages": self._convert_messages_to_api_format(messages)
        }
        
        # Add optional parameters if they are set
        if self.max_tokens is not None:
            # Handle different parameter names for max tokens
            if "o4-mini" in self.api_url:
                payload["max_completion_tokens"] = self.max_tokens
                logger.info(f"Max completion tokens: {self.max_tokens}")
            else:
                payload["max_tokens"] = self.max_tokens
                logger.info(f"Max tokens: {self.max_tokens}")

        if self.temperature is not None:
            payload["temperature"] = self.temperature
            logger.info(f"Temperature: {self.temperature}")
        if self.top_p is not None:
            payload["top_p"] = self.top_p
            logger.info(f"Top-p: {self.top_p}")
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort
            logger.info(f"Reasoning effort: {self.reasoning_effort}")

        logger.info(f"Sending request to: {self.api_url}")
        logger.debug(f"Full request payload:\n{json.dumps(payload, indent=2)}")
        
        # Make the API call
        try:
            logger.info("Making API request...")
            api_start_time = time.time()
            
            response = self.http_client.post(
                self.api_url, 
                json=payload, 
                headers={**headers, "Authorization": f"Bearer {bearer_token}"},  # Use full token for actual request
                timeout=180.0
            )
            
            api_duration = time.time() - api_start_time
            logger.info(f"API request completed in {api_duration:.2f} seconds")
            logger.info(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            logger.error(f"=== WBG LLM API Error ===")
            logger.error(f"Status code: {e.response.status_code}")
            logger.error(f"Error response body:\n{err_text}")
            
            # Try to parse error as JSON for better formatting
            try:
                error_json = json.loads(err_text)
                logger.error(f"Parsed error details:\n{json.dumps(error_json, indent=2)}")
            except:
                logger.error("Could not parse error response as JSON")
            
            logger.error(f"Request URL: {self.api_url}")
            logger.error(f"Request payload:\n{json.dumps(payload, indent=2)}")
            raise WBGAPIError(f"API returned status {e.response.status_code}: {err_text}") from e
            
        except httpx.TimeoutException as e:
            logger.error(f"=== WBG LLM API Timeout ===")
            logger.error(f"Request timed out after 180 seconds")
            logger.error(f"Request URL: {self.api_url}")
            raise WBGAPIError(f"API request timed out: {e}") from e
            
        except Exception as e:
            logger.error(f"=== WBG LLM API Unexpected Error ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.exception("Full error traceback:")
            logger.error(f"Request URL: {self.api_url}")
            logger.error(f"Request payload:\n{json.dumps(payload, indent=2)}")
            raise WBGAPIError(f"An unexpected error occurred during API call: {e}") from e

        # Process the response
        try:
            response_data = response.json()
            logger.debug(f"Response JSON structure: {list(response_data.keys())}")
            
            # Log token usage if available
            if "usage" in response_data:
                usage = response_data["usage"]
                logger.info(f"Token usage - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                           f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                           f"Total: {usage.get('total_tokens', 'N/A')}")
            
            content = response_data["choices"][0]["message"]["content"]
            content_preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Response preview: {content_preview}")
            logger.info(f"Response length: {len(content)} characters")
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse API response")
            logger.error(f"Response text: {response.text}")
            logger.exception("Parse error:")
            raise WBGAPIError(f"Failed to parse API response: {e}") from e
        
        total_duration = time.time() - start_time
        logger.info(f"=== WBG LLM API Request Completed in {total_duration:.2f} seconds ===")
        
        return content

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> Iterator[ChatGenerationChunk]:
        """Stream the response - WBG API doesn't support streaming, so we yield the full response."""
        content = self._call(messages, stop, **kwargs)
        chunk = ChatGenerationChunk(
            message=AIMessageChunk(content=content)
        )
        if run_manager:
            run_manager.on_llm_new_token(content, chunk=chunk)
        yield chunk


def create_wbg_llm(
    model_name: str = "o4-mini", 
    max_tokens: Optional[int] = None,
    auth_manager: Optional[WBGAuthManager] = None,
    **kwargs: Any
) -> WBGChatModel:
    """Factory function to create a configured instance of WBG LLM.
    
    Args:
        model_name: Either "o4-mini" or "gpt-4.1"
        max_tokens: Maximum tokens to generate (will use config or defaults if not specified)
        auth_manager: Optional WBGAuthManager instance for authentication
        **kwargs: Additional model-specific parameters
    
    Returns:
        Configured WBGChatModel instance
    """
    
    endpoints = {
        "o4-mini": "https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview",
        "gpt-4.1": "https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
    }

    if model_name not in endpoints:
        raise ValueError(f"Unknown model name: {model_name}. Available models: {list(endpoints.keys())}")
        
    api_url = endpoints[model_name]
    
    # Set model-specific defaults
    if model_name == "o4-mini" and "reasoning_effort" not in kwargs:
        kwargs["reasoning_effort"] = "medium"
    
    # Pass max_tokens only if provided
    if max_tokens is not None:
        kwargs['max_tokens'] = max_tokens
    
    return WBGChatModel(
        api_url=api_url,
        auth_manager=auth_manager,
        **kwargs
    )