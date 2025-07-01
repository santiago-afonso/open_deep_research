"""Unit tests for the authentication module."""

import os
import pytest
from unittest.mock import patch
from open_deep_research.auth import AuthManager


class TestAuthManager:
    """Test cases for AuthManager class."""
    
    def test_init_with_api_keys(self):
        """Test AuthManager initialization with API keys."""
        api_keys = {
            "openai": "test-openai-key",
            "anthropic": "test-anthropic-key"
        }
        auth_manager = AuthManager(api_keys=api_keys)
        
        assert auth_manager.api_keys == api_keys
    
    def test_init_without_api_keys(self):
        """Test AuthManager initialization without API keys."""
        auth_manager = AuthManager()
        assert auth_manager.api_keys == {}
    
    def test_validate_keys_with_invalid_key(self):
        """Test that invalid API keys raise ValueError."""
        with pytest.raises(ValueError, match="API key for openai must be a string"):
            AuthManager(api_keys={"openai": 123})
        
        with pytest.raises(ValueError, match="API key for anthropic cannot be empty"):
            AuthManager(api_keys={"anthropic": ""})
        
        with pytest.raises(ValueError, match="API key for google cannot be empty"):
            AuthManager(api_keys={"google": "   "})
    
    def test_get_api_key_from_config(self):
        """Test getting API key from configuration."""
        api_keys = {"openai": "test-key"}
        auth_manager = AuthManager(api_keys=api_keys)
        
        assert auth_manager.get_api_key("openai") == "test-key"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-test-key"})
    def test_get_api_key_from_env(self):
        """Test getting API key from environment variable."""
        auth_manager = AuthManager()
        
        assert auth_manager.get_api_key("openai") == "env-test-key"
    
    def test_get_api_key_precedence(self):
        """Test that configured keys take precedence over env vars."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            auth_manager = AuthManager(api_keys={"openai": "config-key"})
            assert auth_manager.get_api_key("openai") == "config-key"
    
    def test_get_api_key_for_provider_without_auth(self):
        """Test getting API key for provider that doesn't need auth."""
        auth_manager = AuthManager()
        assert auth_manager.get_api_key("ollama") is None
    
    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    })
    def test_get_api_key_for_bedrock(self):
        """Test getting API keys for AWS Bedrock."""
        auth_manager = AuthManager()
        keys = auth_manager.get_api_key("bedrock")
        
        assert isinstance(keys, dict)
        assert keys["AWS_ACCESS_KEY_ID"] == "test-access-key"
        assert keys["AWS_SECRET_ACCESS_KEY"] == "test-secret-key"
    
    def test_set_api_key(self):
        """Test setting an API key."""
        auth_manager = AuthManager()
        auth_manager.set_api_key("openai", "new-key")
        
        assert auth_manager.get_api_key("openai") == "new-key"
    
    def test_set_api_key_invalid(self):
        """Test setting invalid API keys."""
        auth_manager = AuthManager()
        
        with pytest.raises(ValueError, match="API key for openai cannot be empty"):
            auth_manager.set_api_key("openai", "")
        
        with pytest.raises(ValueError, match="API key for anthropic cannot be empty"):
            auth_manager.set_api_key("anthropic", "   ")
    
    def test_get_auth_kwargs(self):
        """Test getting authentication kwargs."""
        auth_manager = AuthManager(api_keys={"openai": "test-key"})
        
        kwargs = auth_manager.get_auth_kwargs("openai")
        assert kwargs == {"api_key": "test-key"}
        
        kwargs = auth_manager.get_auth_kwargs("ollama")
        assert kwargs == {}
    
    @patch.dict(os.environ, {}, clear=True)
    def test_ensure_env_vars(self):
        """Test ensuring environment variables are set."""
        auth_manager = AuthManager(api_keys={
            "openai": "test-openai-key",
            "anthropic": "test-anthropic-key"
        })
        
        # Env vars should not be set yet
        assert os.environ.get("OPENAI_API_KEY") is None
        assert os.environ.get("ANTHROPIC_API_KEY") is None
        
        # Ensure env vars
        auth_manager.ensure_env_vars()
        
        # Now they should be set
        assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"
        assert os.environ.get("ANTHROPIC_API_KEY") == "test-anthropic-key"
    
    def test_has_auth_for_provider(self):
        """Test checking if we have auth for a provider."""
        auth_manager = AuthManager(api_keys={"openai": "test-key"})
        
        assert auth_manager.has_auth_for_provider("openai") is True
        assert auth_manager.has_auth_for_provider("anthropic") is False
        assert auth_manager.has_auth_for_provider("ollama") is False  # No auth needed
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"})
    def test_has_auth_for_provider_from_env(self):
        """Test checking auth from environment variables."""
        auth_manager = AuthManager()
        
        assert auth_manager.has_auth_for_provider("anthropic") is True
        assert auth_manager.has_auth_for_provider("openai") is False