Here is a comprehensive guide on how to adapt the open_deep_research LangGraph project to use our organization's private LLM endpoints, covering both authentication and API integration. This document is designed to be a standalone guide for developers working on other projects.

---

# Guide: Integrating a Private LLM API with Your LangGraph Project

This document outlines the steps to adapt a project built with LangChain/LangGraph, which currently uses public APIs (like OpenAI), to work with a secure, private organizational LLM API. We will cover:

1.  **Authentication**: Implementing a robust, long-running authentication flow that requires user interaction only once, then refreshes silently in the background.
2.  **API Integration**: Creating a custom, LangChain-compatible "Chat Model" to handle the specific request and response formats of your organization's private LLM endpoints.

By following this guide, you can create a seamless and secure developer experience for using internal LLM resources.

## Part 1: Authentication - The "Log In Once, Run for Days" Model

Your organization's API is protected by an authentication system (like Microsoft Entra ID) that uses short-lived access tokens. A naive implementation would require the user to log in every hour, which is not feasible for long-running scripts or development.

The solution is to use **Refresh Tokens**, a standard OAuth 2.0 feature.

### Conceptual Overview: The Theme Park Analogy

Imagine a 90-day festival at a theme park:

*   **The Access Token (Day Pass)**: On your first day, you show your ID (username/password/MFA) at the main gate. They give you a Day Pass that works on all rides but expires at midnight. This is your **Access Token**. It's short-lived.
*   **The Refresh Token (Wristband)**: Along with the Day Pass, they give you a durable, long-lasting wristband. Its only purpose is to prove you've already been authenticated. This is your **Refresh Token**.
*   **The Next Day**: Your Day Pass is expired. Instead of going back to the main gate, you go to an automated kiosk, scan your Wristband (Refresh Token), and it instantly prints a new Day Pass for today (a new Access Token).

This can continue for up to 90 days. You only perform the full, interactive login once.

### Implementation: The `AuthManager`

To implement this flow, we'll use an `AuthManager` class. This class encapsulates all the complexity of handling tokens using the Microsoft Authentication Library (MSAL).

**Key Features of `AuthManager`:**

*   Uses the official `msal` library for security and correctness.
*   Manages a secure, local token cache file (`.wbg_token_cache.bin` in this repo).
*   Attempts to acquire a token silently using a stored refresh token.
*   If silent refresh fails (e.g., first run, or refresh token expired), it automatically falls back to an interactive "Device Code Flow".

Here is the code for a reusable `AuthManager` based on the reference repository's `Code/modules/auth_manager.py`. You should create this file in your own project (e.g., `your_project/modules/auth_manager.py`).

```python
# your_project/modules/auth_manager.py

import msal
from loguru import logger
from pathlib import Path
from typing import Optional, Dict, Any

class AuthManager:
    """Manages authentication tokens for WBG APIs using MSAL with automatic refresh."""
    
    def __init__(
        self,
        # These are standard Microsoft Entra ID details for public clients
        tenant_id: str = "31a2fec0-266b-4c67-b56e-2796d8f59c36",
        client_id: str = "00c104af-b0ae-4557-9787-6e6cfced741e",
        scope: str = "https://cognitiveservices.azure.com/.default",
        token_file: Optional[Path] = None
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.scope = scope
        
        if token_file is None:
            # Store the cache in a Temp directory in the project root
            token_file = Path(__file__).parent.parent / "Temp" / ".token_cache.bin"
        self.token_file = token_file
        
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.msal_app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=self._get_token_cache()
        )
        logger.info(f"AuthManager initialized. Cache file: {self.token_file}")

    def _get_token_cache(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if self.token_file.exists():
            try:
                cache.deserialize(open(self.token_file, "r").read())
                logger.debug("Token cache loaded from file.")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")
        return cache

    def _save_token_cache(self) -> None:
        if self.msal_app.token_cache.has_state_changed:
            with open(self.token_file, "w") as f:
                f.write(self.msal_app.token_cache.serialize())
            logger.debug("Token cache saved to file.")

    def get_bearer_token(self) -> str:
        """
        Get a valid bearer token, using silent refresh if possible and falling
        back to interactive flow if necessary.
        """
        accounts = self.msal_app.get_accounts()
        result = None
        
        if accounts:
            logger.info("Account found in cache. Attempting silent token acquisition.")
            result = self.msal_app.acquire_token_silent(scopes=[self.scope], account=accounts[0])
        
        if not result:
            logger.info("Silent acquisition failed. Initiating Device Code Flow for interactive auth.")
            flow = self.msal_app.initiate_device_flow(scopes=[self.scope])
            if "user_code" not in flow:
                raise Exception(f"Failed to create device flow: {flow.get('error_description')}")
            
            print(flow["message"]) # Instruct user to go to a URL and enter a code
            result = self.msal_app.acquire_token_by_device_flow(flow)
            
        if "access_token" in result:
            self._save_token_cache()
            return result["access_token"]
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")

```

### First-Time Setup: Interactive Login

To bootstrap the process, the user must log in interactively once. Create a simple script for this.

```python
# your_project/scripts/generate_token.py

from your_project.modules.auth_manager import AuthManager

def main():
    print("--- Interactive Token Generation ---")
    try:
        auth = AuthManager()
        token = auth.get_bearer_token()
        print("\n✅ Token acquired and cached successfully!")
        print("You can now run your application scripts.")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")

if __name__ == "__main__":
    main()
```

Instruct your users to run `python scripts/generate_token.py` once. This will prompt them to log in with their corporate credentials and will create the `.token_cache.bin` file, enabling subsequent runs to be silent.

## Part 2: API Integration - Creating a Custom LangChain Adapter

LangChain uses "Chat Model" classes to interact with LLMs. To use your organization's custom endpoints, you need to create your own adapter class that inherits from `SimpleChatModel`.

### Analyzing the API Endpoints

You have two models, each with a specific endpoint and slightly different parameters.

**Common Features**:
*   Method: `POST`
*   Header: `Content-Type: application/json`
*   Header: `Authorization: Bearer <token>`
*   Body: A `messages` array with `role` and `content`.

**Model-Specific Parameters**:
*   **o4-mini**: `max_completion_tokens`, `reasoning_effort`
*   **gpt-4.1**: `max_tokens`, `temperature`, `top_p`

Our adapter must be flexible enough to handle these differences.

### Implementation: The `PrivateAPIChatModel`

Let's create a custom chat model adapter. This code is adapted from `Code/modules/llm_adapter.py`.

```python
# your_project/modules/llm_adapter.py

import httpx
import json
from typing import Any, Dict, List, Optional
from pydantic import Field

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from loguru import logger

# Import your AuthManager
from .auth_manager import AuthManager

class PrivateAPIError(Exception):
    """Custom exception for our private API."""
    pass

class PrivateAPIChatModel(SimpleChatModel):
    """LangChain-compatible chat model for our organization's private API."""
    
    # --- Configuration Fields ---
    api_url: str = Field(..., description="The full API endpoint URL.")
    
    # Common parameters
    max_tokens: Optional[int] = Field(default=None)
    
    # gpt-4.1 specific
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)

    # o4-mini specific
    reasoning_effort: Optional[str] = Field(default=None)
    
    # Internal components
    auth_manager: AuthManager = Field(default_factory=AuthManager, exclude=True)
    http_client: httpx.AsyncClient = Field(default_factory=httpx.AsyncClient, exclude=True)

    @property
    def _llm_type(self) -> str:
        return "private_api_chat_model"

    def _convert_messages_to_api_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Converts LangChain messages to the simple list of dicts our API expects."""
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

    async def _acall(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """The main async call method LangChain uses."""
        
        # 1. Get a valid Bearer Token
        try:
            bearer_token = self.auth_manager.get_bearer_token()
        except Exception as e:
            raise PrivateAPIError(f"Authentication failed: {e}") from e

        # 2. Prepare headers
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }

        # 3. Prepare payload with model-specific parameters
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

        logger.debug(f"Calling private API at {self.api_url}")
        
        # 4. Make the API call
        try:
            response = await self.http_client.post(self.api_url, json=payload, headers=headers, timeout=180.0)
            response.raise_for_status() # Raise an exception for 4xx/5xx responses
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            raise PrivateAPIError(f"API returned status {e.response.status_code}: {err_text}") from e
        except Exception as e:
            raise PrivateAPIError(f"An unexpected error occurred during API call: {e}") from e

        # 5. Process the response
        # Assuming the response format is similar to OpenAI's
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        
        return content

```

### Creating a Convenience Function

To make it easy to instantiate your models, create a helper function.

```python
# your_project/modules/llm_adapter.py (continued)

def create_private_llm(
    model_name: str, 
    max_tokens: int = 4096, 
    **kwargs: Any
) -> PrivateAPIChatModel:
    """Factory function to create a configured instance of our private LLM."""
    
    endpoints = {
        "o4-mini": "https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview",
        "gpt-4.1": "https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
    }

    if model_name not in endpoints:
        raise ValueError(f"Unknown model name: {model_name}. Available models: {list(endpoints.keys())}")
        
    api_url = endpoints[model_name]
    
    return PrivateAPIChatModel(api_url=api_url, max_tokens=max_tokens, **kwargs)
```

## Part 3: Putting It All Together in LangGraph

Now, you can seamlessly use your new private LLM adapter within your LangGraph nodes.

### Example: Swapping Models in a Graph Node

Let's say you have a graph node that calls an LLM.

**Before (using a public API):**
```python
from langchain_openai import ChatOpenAI

async def call_model_node(state):
    messages = state["messages"]
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0) # Old way
    response = await llm.ainvoke(messages)
    # ... update state with response
    return {"messages": state["messages"] + [response]}
```

**After (using your private API adapter):**
```python
# Import your new factory function
from your_project.modules.llm_adapter import create_private_llm

async def call_model_node(state):
    messages = state["messages"]
    # New way: instantiate your private model
    llm = create_private_llm(model_name="gpt-4.1", temperature=0.5) 
    response = await llm.ainvoke(messages)
    # ... update state with response
    return {"messages": state["messages"] + [response]}

# Or to use the other model:
async def another_node(state):
    messages = state["messages"]
    llm = create_private_llm(model_name="o4-mini", reasoning_effort="medium")
    response = await llm.ainvoke(messages)
    # ...
    return {"messages": state["messages"] + [response]}
```

### Validating Authentication in Your Orchestrator

It's good practice to validate that authentication is working *before* you start a long-running graph. Add a check at the beginning of your main script.

```python
# your_project/scripts/orchestrator.py

import asyncio
from your_project.modules.auth_manager import AuthManager

async def validate_auth():
    """Ensure we can get a token before starting the main workflow."""
    print("Validating authentication...")
    try:
        auth_manager = AuthManager()
        auth_manager.get_bearer_token()
        print("✅ Authentication successful.")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("Please run 'python scripts/generate_token.py' to log in interactively.")
        exit(1)

async def main():
    await validate_auth()
    # ... your graph execution logic here ...

if __name__ == "__main__":
    asyncio.run(main())
```

This simple check provides a much better user experience by catching authentication issues early.