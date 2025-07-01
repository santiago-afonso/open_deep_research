"""Authentication module for managing API keys across different LLM providers."""

import os
from typing import Dict, Optional, Any
from .logging_config import logger


class AuthManager:
    """Manages API keys and authentication for various LLM providers."""
    
    # Mapping of provider names to their environment variable names
    PROVIDER_ENV_VARS = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "google_genai": "GOOGLE_API_KEY",
        "google_vertexai": "GOOGLE_APPLICATION_CREDENTIALS",
        "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"],
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "ollama": None,  # No API key needed
        "deepseek": "DEEPSEEK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "nvidia": "NVIDIA_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "ai21": "AI21_API_KEY",
        "cohere": "COHERE_API_KEY"
    }
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the AuthManager.
        
        Args:
            api_keys: Optional dictionary of provider names to API keys.
                     If not provided, will use environment variables.
        """
        self.api_keys = api_keys or {}
        logger.info("=== AuthManager Initialized ===")
        if self.api_keys:
            logger.info(f"Configured providers: {list(self.api_keys.keys())}")
        else:
            logger.info("No API keys provided, will use environment variables")
        self._validate_keys()
    
    def _validate_keys(self):
        """Validate that provided API keys are non-empty strings."""
        for provider, key in self.api_keys.items():
            if key and not isinstance(key, str):
                logger.error(f"Invalid API key type for {provider}: {type(key)}")
                raise ValueError(f"API key for {provider} must be a string")
            if key and not key.strip():
                logger.error(f"Empty API key provided for {provider}")
                raise ValueError(f"API key for {provider} cannot be empty")
            logger.debug(f"Validated API key for {provider}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        First checks if a key was provided in the constructor,
        then falls back to environment variables.
        
        Args:
            provider: The provider name (e.g., 'openai', 'anthropic')
            
        Returns:
            The API key if found, None otherwise
        """
        logger.debug(f"Getting API key for provider: {provider}")
        
        # First check if we have a configured key
        if provider in self.api_keys:
            logger.debug(f"Using configured API key for {provider}")
            return self.api_keys[provider]
        
        # Fall back to environment variables
        env_var = self.PROVIDER_ENV_VARS.get(provider)
        
        if env_var is None:
            # Provider doesn't need authentication (e.g., ollama)
            logger.debug(f"Provider {provider} doesn't require authentication")
            return None
        
        if isinstance(env_var, list):
            # Special case for providers that need multiple env vars (e.g., bedrock)
            logger.debug(f"Provider {provider} requires multiple environment variables: {env_var}")
            keys = {}
            for var in env_var:
                value = os.getenv(var)
                if value:
                    keys[var] = value
                    logger.debug(f"Found environment variable {var}")
                else:
                    logger.debug(f"Environment variable {var} not set")
            
            if keys:
                logger.info(f"Found {len(keys)} of {len(env_var)} required environment variables for {provider}")
                return keys
            else:
                logger.warning(f"No environment variables found for {provider}")
                return None
        
        # Single environment variable
        value = os.getenv(env_var)
        if value:
            logger.info(f"Found API key for {provider} in environment variable {env_var}")
        else:
            logger.debug(f"Environment variable {env_var} not set for {provider}")
        
        return value
    
    def set_api_key(self, provider: str, api_key: str):
        """
        Set API key for a specific provider.
        
        Args:
            provider: The provider name
            api_key: The API key to set
        """
        logger.info(f"Setting API key for provider: {provider}")
        
        if not api_key or not api_key.strip():
            logger.error(f"Attempted to set empty API key for {provider}")
            raise ValueError(f"API key for {provider} cannot be empty")
        
        self.api_keys[provider] = api_key
        logger.info(f"Successfully set API key for {provider}")
    
    def get_auth_kwargs(self, provider: str) -> Dict[str, Any]:
        """
        Get authentication kwargs for a specific provider.
        
        Args:
            provider: The provider name
            
        Returns:
            Dictionary of authentication parameters to pass to the model
        """
        api_key = self.get_api_key(provider)
        
        if api_key is None:
            return {}
        
        # Special handling for different providers
        if provider == "bedrock" and isinstance(api_key, dict):
            # AWS credentials are handled differently
            return {}  # AWS SDK will pick up env vars automatically
        
        # Most providers use 'api_key' parameter
        return {"api_key": api_key}
    
    def ensure_env_vars(self):
        """
        Ensure all configured API keys are set as environment variables.
        This is useful for libraries that directly read from env vars.
        """
        for provider, api_key in self.api_keys.items():
            if not api_key:
                continue
                
            env_var = self.PROVIDER_ENV_VARS.get(provider)
            if env_var and isinstance(env_var, str):
                os.environ[env_var] = api_key
                logger.debug(f"Set {env_var} environment variable")
    
    def has_auth_for_provider(self, provider: str) -> bool:
        """
        Check if we have authentication credentials for a provider.
        
        Args:
            provider: The provider name
            
        Returns:
            True if we have credentials, False otherwise
        """
        return self.get_api_key(provider) is not None