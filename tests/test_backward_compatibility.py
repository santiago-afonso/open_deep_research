"""Test backward compatibility of the authentication system."""

import os
import pytest
from unittest.mock import patch, Mock
from open_deep_research.api_adapter import init_authenticated_chat_model
from open_deep_research.auth import AuthManager
from open_deep_research.configuration import WorkflowConfiguration, MultiAgentConfiguration


class TestBackwardCompatibility:
    """Test that existing functionality continues to work."""
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_env_var_fallback(self, mock_init_chat_model):
        """Test that models work with environment variables when no API keys configured."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        # Simulate environment with API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            # Initialize without any auth configuration
            result = init_authenticated_chat_model("gpt-4")
            
            # Should still work using env var
            mock_init_chat_model.assert_called_once_with("gpt-4")
            assert result == mock_model
    
    def test_configuration_without_api_keys(self):
        """Test that configuration classes work without api_keys field."""
        # WorkflowConfiguration
        workflow_config = WorkflowConfiguration(
            planner_model="gpt-4",
            writer_model="gpt-3.5-turbo"
        )
        assert workflow_config.api_keys is None
        
        # MultiAgentConfiguration
        multi_agent_config = MultiAgentConfiguration(
            supervisor_model="openai:gpt-4",
            researcher_model="anthropic:claude-3"
        )
        assert multi_agent_config.api_keys is None
    
    def test_configuration_with_api_keys(self):
        """Test that configuration classes accept api_keys field."""
        api_keys = {"openai": "test-key", "anthropic": "test-key-2"}
        
        # WorkflowConfiguration
        workflow_config = WorkflowConfiguration(
            planner_model="gpt-4",
            api_keys=api_keys
        )
        assert workflow_config.api_keys == api_keys
        
        # MultiAgentConfiguration  
        multi_agent_config = MultiAgentConfiguration(
            supervisor_model="openai:gpt-4",
            api_keys=api_keys
        )
        assert multi_agent_config.api_keys == api_keys
    
    @patch('open_deep_research.api_adapter.init_chat_model')
    def test_all_providers_support(self, mock_init_chat_model):
        """Test that all supported providers work correctly."""
        mock_model = Mock()
        mock_init_chat_model.return_value = mock_model
        
        providers_and_models = [
            ("gpt-4", "openai"),
            ("claude-3-opus", "anthropic"),
            ("gemini-pro", "google_genai"),
            ("llama-2-70b", "ollama"),
            ("mistral-7b", "mistral"),
            ("deepseek-coder", "deepseek"),
            ("openai:gpt-4", "openai"),
            ("anthropic:claude-3", "anthropic"),
        ]
        
        for model, expected_provider in providers_and_models:
            mock_init_chat_model.reset_mock()
            
            # Create auth manager with key for the provider
            auth_manager = AuthManager(api_keys={expected_provider: f"test-key-{expected_provider}"})
            
            # Initialize model
            result = init_authenticated_chat_model(model, auth_manager=auth_manager)
            
            # Verify it was called correctly
            if expected_provider == "ollama":
                # Ollama doesn't need API key
                mock_init_chat_model.assert_called_once_with(model)
            else:
                mock_init_chat_model.assert_called_once_with(
                    model, 
                    api_key=f"test-key-{expected_provider}"
                )
            
            assert result == mock_model
    
    def test_auth_manager_provider_list(self):
        """Test that AuthManager supports all documented providers."""
        expected_providers = [
            "openai", "anthropic", "google_genai", "google_vertexai",
            "bedrock", "groq", "together", "ollama", "deepseek",
            "openrouter", "fireworks", "nvidia", "mistral", "ai21", "cohere"
        ]
        
        for provider in expected_providers:
            assert provider in AuthManager.PROVIDER_ENV_VARS
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_env_vars_no_config(self):
        """Test behavior when no env vars or config provided."""
        auth_manager = AuthManager()
        
        # Should return None for providers that need auth
        assert auth_manager.get_api_key("openai") is None
        assert auth_manager.get_api_key("anthropic") is None
        
        # Should return empty dict for auth kwargs
        assert auth_manager.get_auth_kwargs("openai") == {}
        assert auth_manager.get_auth_kwargs("anthropic") == {}