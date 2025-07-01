# Authentication and API Key Management

This document explains how to use the new authentication system in Open Deep Research, which provides flexible API key management for multiple LLM providers.

## Overview

The authentication system provides three ways to manage API keys:

1. **Environment Variables** (default, backward compatible)
2. **Configuration-based API Keys** (pass keys directly in config)
3. **Global AuthManager** (set once, use everywhere)

## Quick Start

### Method 1: Environment Variables (No Changes Needed)

Continue using your `.env` file as before:

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

Your existing code continues to work without any changes.

### Method 2: Configuration API Keys

Pass API keys directly in the configuration:

```python
from open_deep_research.graph import graph

# Define your API keys
api_keys = {
    "openai": "your-openai-key",
    "anthropic": "your-anthropic-key",
    "google_genai": "your-google-key"
}

# Use them in configuration
result = await graph.ainvoke(
    {"topic": "AI in healthcare"},
    {"configurable": {
        "api_keys": api_keys,  # Pass keys here
        "planner_model": "gpt-4",
        "writer_model": "claude-3-opus"
    }}
)
```

### Method 3: Global AuthManager

Set up authentication once for your entire application:

```python
from open_deep_research.auth import AuthManager
from open_deep_research.api_adapter import set_global_auth_manager

# Create auth manager
auth_manager = AuthManager(api_keys={
    "openai": "your-openai-key",
    "anthropic": "your-anthropic-key"
})

# Set it globally
set_global_auth_manager(auth_manager)

# Now all models will use these keys automatically
```

## Supported Providers

The authentication system supports all major LLM providers:

| Provider | Environment Variable | Model Examples |
|----------|---------------------|----------------|
| OpenAI | `OPENAI_API_KEY` | gpt-4, gpt-3.5-turbo |
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet |
| Google GenAI | `GOOGLE_API_KEY` | gemini-pro, gemini-1.5-pro |
| Google Vertex AI | `GOOGLE_APPLICATION_CREDENTIALS` | gemini-pro (vertex) |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | anthropic.claude-v2 |
| Groq | `GROQ_API_KEY` | llama2-70b-4096 |
| Together AI | `TOGETHER_API_KEY` | various open models |
| Ollama | None (local) | llama2, mistral |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-coder |
| OpenRouter | `OPENROUTER_API_KEY` | various models |
| Fireworks | `FIREWORKS_API_KEY` | various models |
| NVIDIA | `NVIDIA_API_KEY` | various models |
| Mistral | `MISTRAL_API_KEY` | mistral-tiny, mistral-small |
| AI21 | `AI21_API_KEY` | j2-grande, j2-jumbo |
| Cohere | `COHERE_API_KEY` | command, command-light |

## Advanced Usage

### Mixing Authentication Methods

You can mix different authentication methods. Configuration keys take precedence:

```python
# OPENAI_API_KEY is in .env
# We'll provide Anthropic key via config

api_keys = {
    "anthropic": "your-anthropic-key"  # Override for Anthropic only
}

# OpenAI will use env var, Anthropic will use config key
```

### Provider Auto-Detection

The system automatically detects providers from model names:

```python
# These are automatically detected:
"gpt-4"              # -> openai
"claude-3-opus"      # -> anthropic  
"gemini-pro"         # -> google_genai
"llama2"             # -> ollama

# Or use explicit format:
"openai:gpt-4"
"anthropic:claude-3"
```

### Checking Authentication Status

```python
from open_deep_research.auth import AuthManager

auth = AuthManager(api_keys={"openai": "test-key"})

# Check if we have auth for a provider
if auth.has_auth_for_provider("openai"):
    print("OpenAI is configured")

# Get auth kwargs for a provider
kwargs = auth.get_auth_kwargs("openai")  # {"api_key": "test-key"}
```

### Programmatic Key Management

```python
auth = AuthManager()

# Set keys programmatically
auth.set_api_key("openai", "new-key")
auth.set_api_key("anthropic", "another-key")

# Ensure environment variables are updated
auth.ensure_env_vars()  # Sets OPENAI_API_KEY, ANTHROPIC_API_KEY
```

## Migration Guide

### From Environment Variables

No changes needed! Your existing setup continues to work.

### Adding Configuration Keys

To start using configuration-based keys:

1. Add `api_keys` to your configuration classes:

```python
# Before
config = {
    "planner_model": "gpt-4",
    "writer_model": "claude-3"
}

# After  
config = {
    "planner_model": "gpt-4",
    "writer_model": "claude-3",
    "api_keys": {
        "openai": "your-key",
        "anthropic": "your-key"
    }
}
```

2. Pass the configuration when invoking graphs:

```python
result = await graph.ainvoke(
    {"topic": "Your topic"},
    {"configurable": config}
)
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for production deployments
3. **Rotate keys regularly**
4. **Use separate keys** for development and production
5. **Limit key permissions** when possible

## Troubleshooting

### "API key not found" errors

1. Check environment variables are set:
   ```python
   import os
   print(os.getenv("OPENAI_API_KEY"))
   ```

2. Verify configuration keys:
   ```python
   print(config.get("api_keys", {}).get("openai"))
   ```

3. Check auth manager:
   ```python
   auth = AuthManager()
   print(auth.get_api_key("openai"))
   ```

### Provider detection issues

If a model isn't detected correctly, use explicit provider format:

```python
# Instead of
model = "custom-model"

# Use
model = "openai:custom-model"
```

## Examples

See the `examples/using_api_keys.py` file for complete working examples of all authentication methods.