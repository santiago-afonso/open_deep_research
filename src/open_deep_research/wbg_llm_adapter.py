"""WBG LLM Adapter for private API endpoints."""

import httpx
import json
from typing import Any, Dict, List, Optional, Iterator
from pydantic import Field

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from loguru import logger

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
    auth_manager: WBGAuthManager = Field(default_factory=WBGAuthManager, exclude=True)
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
        # Get a valid Bearer Token
        try:
            bearer_token = self.auth_manager.get_bearer_token()
        except Exception as e:
            raise WBGAPIError(f"Authentication failed: {e}") from e

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }

        # Prepare payload with model-specific parameters
        payload = {
            "messages": self._convert_messages_to_api_format(messages)
        }
        
        # Add optional parameters if they are set
        if self.max_tokens is not None:
            # Handle different parameter names for max tokens
            if "o4-mini" in self.api_url:
                payload["max_completion_tokens"] = self.max_tokens
            else:
                payload["max_tokens"] = self.max_tokens

        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort

        logger.debug(f"Calling WBG API at {self.api_url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Make the API call
        try:
            response = self.http_client.post(
                self.api_url, 
                json=payload, 
                headers=headers, 
                timeout=180.0
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            raise WBGAPIError(f"API returned status {e.response.status_code}: {err_text}") from e
        except Exception as e:
            raise WBGAPIError(f"An unexpected error occurred during API call: {e}") from e

        # Process the response
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        
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
    max_tokens: int = 100000,
    **kwargs: Any
) -> WBGChatModel:
    """Factory function to create a configured instance of WBG LLM.
    
    Args:
        model_name: Either "o4-mini" or "gpt-4.1"
        max_tokens: Maximum tokens to generate (default: 100000 for o4-mini)
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
    
    return WBGChatModel(
        api_url=api_url, 
        max_tokens=max_tokens, 
        **kwargs
    )