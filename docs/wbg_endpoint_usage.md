# WBG Private LLM Endpoint Configuration Guide

This guide explains how to configure and use the World Bank Group's private LLM endpoints (o4-mini and gpt-4.1) with Open Deep Research.

## Overview

The system is now configured to use WBG's private services by default:
- **LLM Model**: o4-mini with a maximum output of 100,000 tokens
- **Search Provider**: WBG Google Search API for secure web searches

This provides access to high-quality language models and search capabilities through the organization's secure endpoints.

## Quick Start

### 1. Generate Authentication Token

First, you need to authenticate with Microsoft Entra ID to access the WBG endpoints:

```bash
python scripts/generate_token.py
```

This will:
- Open a browser for Microsoft authentication
- Display a device code to enter
- Save a refresh token that lasts up to 90 days
- Store the token in `.wbg_token_cache.bin`

You only need to do this once every 90 days.

### 2. Run the CLI

After authentication, you can use the CLI normally:

```bash
python cli.py --prompt system_prompt.txt --country "Angola"
```

The system will automatically:
- Use the WBG o4-mini model
- Apply the 100,000 token limit
- Use WBG Google Search for web searches
- Handle token refresh as needed

## Configuration Details

### Default Settings

The system is pre-configured with:
- **Model**: o4-mini
- **Max Tokens**: 100,000
- **Provider**: WBG private endpoints
- **Authentication**: Microsoft Entra ID with refresh tokens

### Available Models

Two models are available through WBG endpoints:

1. **o4-mini** (Default)
   - Endpoint: `https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/o4-mini/chat/completions`
   - Supports up to 100,000 completion tokens
   - Parameter: `max_completion_tokens`
   - Optional: `reasoning_effort` (low/medium/high)

2. **gpt-4.1**
   - Endpoint: `https://azapimdev.worldbank.org/conversationalai/v2/openai/deployments/gpt-4.1/chat/completions`
   - Supports standard OpenAI parameters
   - Parameters: `max_tokens`, `temperature`, `top_p`

### Configuration Files

The WBG models are configured as defaults in:
- `src/open_deep_research/configuration.py`
  - `WorkflowConfiguration`: Sets planner and writer models to "o4-mini"
  - `MultiAgentConfiguration`: Sets supervisor and researcher models to "wbg:o4-mini"
  - Both include `wbg_max_tokens: int = 100000`

### Advanced Configuration

To use different settings, you can:

1. **Change the model** in configuration:
   ```python
   # For gpt-4.1 instead of o4-mini
   planner_model: str = "gpt-4.1"
   writer_model: str = "gpt-4.1"
   ```

2. **Adjust token limits**:
   ```python
   # In configuration classes
   wbg_max_tokens: int = 50000  # Reduce if needed
   ```

3. **Use environment variables** to override:
   ```bash
   export PLANNER_MODEL=gpt-4.1
   export WBG_MAX_TOKENS=50000
   ```

## Authentication Details

### How It Works

1. **Initial Authentication**: Run `scripts/generate_token.py`
2. **Device Code Flow**: Follow the URL and enter the code
3. **Token Storage**: Tokens saved in `.wbg_token_cache.bin`
4. **Automatic Refresh**: The system handles token refresh for 90 days
5. **Re-authentication**: After 90 days, run the script again

### Token File Location

The token cache is stored at:
```
/home/safonso/open_deep_research/.wbg_token_cache.bin
```

Keep this file secure and don't commit it to version control.

### Troubleshooting Authentication

If you encounter authentication issues:

1. **Delete the cache file** and re-authenticate:
   ```bash
   rm .wbg_token_cache.bin
   python scripts/generate_token.py
   ```

2. **Check network access** to:
   - `login.microsoftonline.com`
   - `azapimdev.worldbank.org`

3. **Verify your account** has access to the WBG Conversational AI services

## Integrated WBG Services

Open Deep Research now integrates multiple WBG services:

### 1. WBG LLM Models
- **o4-mini**: High-capacity model with 100,000 token output
- **gpt-4.1**: Alternative model with standard capabilities

### 2. WBG Google Search API
- Secure web search through WBG infrastructure
- Configured as default search provider
- Same authentication token as LLM models

### Benefits of Integration
- **Single Authentication**: One token for all WBG services
- **Consistent Security**: All services follow WBG security standards
- **Optimized Performance**: Services designed to work together
- **Simplified Configuration**: Pre-configured defaults for WBG users

## Integration with Open Deep Research

The WBG models integrate seamlessly with both research implementations:

### Graph-based Workflow
- Planner model: Uses o4-mini for generating report structures
- Writer model: Uses o4-mini for content generation
- Both support the 100,000 token limit

### Multi-Agent System
- Supervisor: Manages research using o4-mini
- Researchers: Generate content using o4-mini
- Full parallel processing support

## Example Usage

### Basic Report Generation
```bash
# Authenticate (first time only)
python scripts/generate_token.py

# Generate report for Angola
python cli.py --prompt system_prompt.txt --country "Angola"

# Generate report with auto-accept
python cli.py --prompt system_prompt.txt --country "Brazil" --auto-accept-plan
```

### Batch Processing
```bash
# Generate reports for multiple countries
for country in "Angola" "Kenya" "Nigeria"; do
    python cli.py --prompt system_prompt.txt --country "$country" --auto-accept-plan
done
```

## Security Considerations

1. **Token Security**: The `.wbg_token_cache.bin` file contains sensitive tokens. Never share or commit this file.

2. **Network Security**: All communications use HTTPS with proper certificate validation.

3. **Credential Scope**: The authentication uses minimal scopes required for the Cognitive Services API.

4. **Automatic Timeout**: Tokens expire after 90 days as a security measure.

## Limitations

1. **Token Limit**: While o4-mini supports 100,000 tokens, very large reports may need to be split.

2. **API Rate Limits**: The WBG endpoints may have rate limits. The system includes automatic retry logic.

3. **Network Dependency**: Requires connectivity to WBG services and Microsoft authentication.

4. **Model Availability**: Only o4-mini and gpt-4.1 are available through WBG endpoints.

## Support

For issues specific to:
- **Authentication**: Contact your IT administrator for Microsoft Entra ID access
- **API Access**: Verify you have permissions for the Conversational AI service
- **Implementation**: See the main Open Deep Research documentation