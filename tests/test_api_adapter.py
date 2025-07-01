"""Unit tests for the API adapter module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from open_deep_research.api_adapter import (
    get_provider_from_model,
    init_authenticated_chat_model,
    set_global_auth_manager,
    _global_auth_manager
)
from open_deep_research.auth import AuthManager


class TestProviderDetection:
    """Test cases for provider detection from model names."""
    
    def test_openai_models(self):
        """Test detection of OpenAI models."""
        assert get_provider_from_model("gpt-4") == "openai"
        assert get_provider_from_model("gpt-3.5-turbo") == "openai"
        assert get_provider_from_model("gpt-4-turbo") == "openai"
        assert get_provider_from_model("o1-preview") == "openai"
        assert get_provider_from_model("o1-mini") == "openai"
    
    def test_anthropic_models(self):
        """Test detection of Anthropic models."""
        assert get_provider_from_model("claude-3-opus") == "anthropic"
        assert get_provider_from_model("claude-3-sonnet") == "anthropic"
        assert get_provider_from_model("claude-2.1") == "anthropic"
        assert get_provider_from_model("claude-instant") == "anthropic"
    
    def test_google_models(self):
        """Test detection of Google models."""
        assert get_provider_from_model("gemini-pro") == "google_genai"
        assert get_provider_from_model("gemini-pro-vision") == "google_genai"
        assert get_provider_from_model("gemini-1.5-pro") == "google_genai"
    
    def test_other_providers(self):
        """Test detection of other providers."""
        assert get_provider_from_model("llama-2-70b") == "ollama"
        assert get_provider_from_model("mistral-7b") == "mistral"
        assert get_provider_from_model("deepseek-coder") == "deepseek"
    
    def test_provider_colon_format(self):
        """Test detection with provider:model format."""
        assert get_provider_from_model("openai:gpt-4") == "openai"
        assert get_provider_from_model("anthropic:claude-3") == "anthropic"
        assert get_provider_from_model("custom:model") == "custom"
    
    def test_unknown_model(self):
        """Test default to openai for unknown models."""
        assert get_provider_from_model("unknown-model") == "openai"
        assert get_provider_from_model("some-random-name") == "openai"


class TestGlobalAuthManager:
    """Test cases for global auth manager functionality."""
    
    def test_set_global_auth_manager(self):
        """Test setting global auth manager."""
        auth_manager = AuthManager(api_keys={"openai": "test-key"})
        set_global_auth_manager(auth_manager)
        
        # Check that global is set (we'd need to import _global_auth_manager)
        # For now, this just ensures the function runs without error
    
    def test_global_auth_manager_none_by_default(self):
        """Test that global auth manager is None by default."""
        # This would require resetting the global state
        # In practice, we'd use a fixture to reset globals between tests
        pass


class TestInitAuthenticatedChatModel:
    """Test cases for init_authenticated_chat_model function."""
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_basic_initialization(self, mock_init_chat_model):
        """Test basic model initialization without auth."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        result = init_authenticated_chat_model("gpt-4")
        
        mock_init_chat_model.assert_called_once_with("gpt-4")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_initialization_with_api_key(self, mock_init_chat_model):
        """Test model initialization with explicit API key."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        result = init_authenticated_chat_model("gpt-4", api_key="test-key")
        
        mock_init_chat_model.assert_called_once_with("gpt-4", api_key="test-key")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_initialization_with_auth_manager(self, mock_init_chat_model):
        """Test model initialization with auth manager."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        auth_manager = AuthManager(api_keys={"openai": "manager-key"})
        result = init_authenticated_chat_model("gpt-4", auth_manager=auth_manager)
        
        mock_init_chat_model.assert_called_once_with("gpt-4", api_key="manager-key")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_api_key_precedence(self, mock_init_chat_model):
        """Test that explicit api_key takes precedence over auth_manager."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        auth_manager = AuthManager(api_keys={"openai": "manager-key"})
        result = init_authenticated_chat_model(
            "gpt-4", 
            api_key="explicit-key",
            auth_manager=auth_manager
        )
        
        mock_init_chat_model.assert_called_once_with("gpt-4", api_key="explicit-key")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_kwargs_precedence(self, mock_init_chat_model):
        """Test that kwargs take precedence over auth kwargs."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        auth_manager = AuthManager(api_keys={"openai": "manager-key"})
        result = init_authenticated_chat_model(
            "gpt-4",
            auth_manager=auth_manager,
            api_key="kwargs-key",
            temperature=0.7
        )
        
        mock_init_chat_model.assert_called_once_with(
            "gpt-4", 
            api_key="kwargs-key",
            temperature=0.7
        )
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_model_name_mapping(self, mock_init_chat_model):
        """Test special model name mapping."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        result = init_authenticated_chat_model("claude-3-7-sonnet-latest")
        
        # Should map to specific version
        mock_init_chat_model.assert_called_once_with("claude-3-5-sonnet-20241022")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_explicit_provider(self, mock_init_chat_model):
        """Test initialization with explicit provider."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        auth_manager = AuthManager(api_keys={"custom_provider": "test-key"})
        result = init_authenticated_chat_model(
            "some-model",
            provider="custom_provider",
            auth_manager=auth_manager
        )
        
        mock_init_chat_model.assert_called_once_with("some-model", api_key="test-key")
        assert result == mock_model
    
    @patch('open_deep_research.api_adapter._global_auth_manager')
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_global_auth_manager_usage(self, mock_init_chat_model, mock_global_auth):
        """Test using global auth manager when no auth_manager provided."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        # Set up global auth manager
        global_auth = AuthManager(api_keys={"openai": "global-key"})
        mock_global_auth.return_value = global_auth
        
        # Initialize without providing auth_manager
        result = init_authenticated_chat_model("gpt-4")
        
        # Should use global auth manager's key
        # Note: This test is simplified; actual implementation might differ
        assert result == mock_model