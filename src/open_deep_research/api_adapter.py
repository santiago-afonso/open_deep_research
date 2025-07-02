"""API adapter module that wraps LangChain's init_chat_model with authentication support."""

from typing import Any, Dict, Optional, Union
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from loguru import logger

from .auth import AuthManager


# Global auth manager instance - can be configured once and reused
_global_auth_manager: Optional[AuthManager] = None


def set_global_auth_manager(auth_manager: AuthManager):
    """
    Set a global AuthManager instance to be used by all model initializations.
    
    Args:
        auth_manager: The AuthManager instance to use globally
    """
    global _global_auth_manager
    _global_auth_manager = auth_manager
    logger.info("Global AuthManager configured")


def get_provider_from_model(model: str) -> str:
    """
    Determine the provider from the model string.
    
    Args:
        model: The model string (e.g., 'gpt-4', 'claude-3-sonnet')
        
    Returns:
        The provider name
    """
    model_lower = model.lower()
    
    # Check for WBG models first
    if model_lower in ["o4-mini", "gpt-4.1"]:
        return "wbg"
    # Check for specific model patterns
    elif model_lower.startswith("gpt-") or model_lower in ["o1-preview", "o1-mini"]:
        return "openai"
    elif model_lower.startswith("claude-"):
        return "anthropic"
    elif model_lower.startswith("gemini-"):
        return "google_genai"
    elif model_lower.startswith("llama"):
        return "ollama"  # Default llama to ollama, but could be others
    elif model_lower.startswith("mistral"):
        return "mistral"
    elif model_lower.startswith("deepseek"):
        return "deepseek"
    elif ":" in model:
        # Format like "provider:model"
        return model.split(":")[0]
    else:
        # Default to openai for unknown models
        logger.warning(f"Could not determine provider for model '{model}', defaulting to openai")
        return "openai"


def init_authenticated_chat_model(
    model: str,
    *,
    api_key: Optional[str] = None,
    auth_manager: Optional[AuthManager] = None,
    provider: Optional[str] = None,
    config: Optional[RunnableConfig] = None,
    **kwargs: Any
) -> BaseChatModel:
    """
    Initialize a chat model with authentication support.
    
    This is a drop-in replacement for langchain_community.chat_models.init_chat_model
    that adds authentication management and WBG model support.
    
    Args:
        model: The model name/identifier
        api_key: Optional API key to use for this specific model
        auth_manager: Optional AuthManager instance (uses global if not provided)
        provider: Optional provider name (auto-detected if not provided)
        config: Optional RunnableConfig to get WBG configuration
        **kwargs: Additional arguments passed to init_chat_model
        
    Returns:
        An initialized chat model instance
    """
    # Determine provider if not explicitly provided
    if provider is None:
        provider = get_provider_from_model(model)
    
    # Handle WBG models specially
    if provider == "wbg":
        from .wbg_llm_adapter import create_wbg_llm
        from .wbg_auth_manager import WBGAuthManager
        
        # Get WBG-specific configuration
        max_tokens = kwargs.pop('max_tokens', None) or kwargs.pop('max_completion_tokens', None)
        
        # Check if we have config for WBG-specific settings
        if config and hasattr(config, 'configurable'):
            from .configuration import WorkflowConfiguration, MultiAgentConfiguration
            
            # Try to get configuration
            try:
                wf_config = WorkflowConfiguration.from_runnable_config(config)
                if hasattr(wf_config, 'wbg_max_tokens'):
                    max_tokens = max_tokens or wf_config.wbg_max_tokens
            except:
                try:
                    ma_config = MultiAgentConfiguration.from_runnable_config(config)
                    if hasattr(ma_config, 'wbg_max_tokens'):
                        max_tokens = max_tokens or ma_config.wbg_max_tokens
                except:
                    pass
        
        # Use default max_tokens only if not specified anywhere
        max_tokens = max_tokens or 100000
        
        # Create WBG auth manager - check if api_keys has WBG-specific auth info
        wbg_auth_manager = None
        if auth_manager and hasattr(auth_manager, 'api_keys') and 'wbg' in auth_manager.api_keys:
            # In future, we could support custom WBG auth params from api_keys
            # For now, we'll use the default WBGAuthManager
            logger.info("Using configured WBG authentication")
        
        # Always create WBGAuthManager for now (maintains current behavior)
        wbg_auth_manager = WBGAuthManager()
        
        logger.info(f"Initializing WBG model '{model}' with max_tokens={max_tokens}")
        return create_wbg_llm(model_name=model, max_tokens=max_tokens, auth_manager=wbg_auth_manager, **kwargs)
    
    # For non-WBG models, use the standard flow
    # Use provided auth manager or fall back to global
    auth_mgr = auth_manager or _global_auth_manager
    
    # Get authentication kwargs if we have an auth manager
    auth_kwargs = {}
    if auth_mgr:
        auth_kwargs = auth_mgr.get_auth_kwargs(provider)
        # Ensure environment variables are set for libraries that need them
        auth_mgr.ensure_env_vars()
    
    # If a specific api_key was provided, it takes precedence
    if api_key:
        auth_kwargs = {"api_key": api_key}
    
    # Merge auth kwargs with other kwargs (other kwargs take precedence)
    final_kwargs = {**auth_kwargs, **kwargs}
    
    # Handle special case for models with specific naming
    final_model = model
    if model == "claude-3-7-sonnet-latest":
        final_model = "claude-3-5-sonnet-20241022"
        logger.debug(f"Mapped {model} to {final_model}")
    
    # Log what we're initializing (without exposing keys)
    logger.debug(f"Initializing model '{final_model}' with provider '{provider}'")
    
    # Initialize the model
    return init_chat_model(final_model, **final_kwargs)


# Create a convenience alias for backward compatibility
init_chat_model_with_auth = init_authenticated_chat_model