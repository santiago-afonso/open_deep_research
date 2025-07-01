# WBG Google Search API Usage Guide

This guide explains how to use the World Bank Group's Google Search API integration with Open Deep Research.

## Overview

The WBG Google Search API provides a secure, authenticated way to perform web searches through the World Bank Group's infrastructure. It leverages Google's search capabilities while maintaining organizational security standards.

## Key Features

- **Secure Authentication**: Uses WBG Bearer token authentication
- **High-Quality Results**: Leverages Google's search algorithm
- **Configurable Results**: Specify the number of results per query
- **Structured Output**: Returns results in a consistent JSON format
- **Integrated by Default**: Set as the default search provider

## Configuration

The WBG Google Search is now configured as the default search provider in Open Deep Research. No additional configuration is needed if you want to use it.

### Using WBG Google Search

The system is pre-configured to use WBG Google Search. Simply run your reports as usual:

```bash
python cli.py --prompt system_prompt.txt --country "Angola"
```

### Switching to Other Search Providers

If you need to use a different search provider, you can override the default:

```python
# In configuration
search_api: SearchAPI = SearchAPI.TAVILY  # Or any other supported provider
```

Or via environment variable:
```bash
export SEARCH_API=tavily
```

## Authentication

WBG Google Search uses the same authentication system as other WBG services:

1. **Generate Token** (if not already done):
   ```bash
   python scripts/generate_token.py
   ```

2. The token is automatically used for all WBG Google Search requests

## API Details

### Endpoint
- **DEV**: `https://azapimdev.worldbank.org/conversationalai/platform/google_search/`

### Request Format
```json
{
  "query": "Your search query here",
  "num_results": 5
}
```

### Response Format
```json
[
  {
    "title": "Page Title",
    "link": "https://example.com",
    "snippet": "Brief description of the content..."
  }
]
```

## Usage in Open Deep Research

### Graph-based Workflow

The WBG Google Search is automatically used when configured:

```python
# Default configuration uses WBG Google
search_api: SearchAPI = SearchAPI.WBG_GOOGLE
```

### Multi-Agent System

The multi-agent system fully supports WBG Google Search:

```python
# Automatically uses WBG Google when configured
supervisor_model: str = "wbg:o4-mini"
researcher_model: str = "wbg:o4-mini"
```

## Important Security Considerations

⚠️ **IMPORTANT**: Do not include World Bank-related Organizational Unit (OU) or higher data classification information in your search queries. The system should trim such information before passing queries to the API.

### Examples of What NOT to Search

❌ **Bad**: "World Bank internal project ID ABC123 budget analysis"
✅ **Good**: "Budget analysis best practices for development projects"

❌ **Bad**: "WBG confidential report on country X economic forecast"
✅ **Good**: "Economic forecast methodologies for emerging markets"

## Comparison with Other Search Providers

| Feature | WBG Google | Tavily | DuckDuckGo | Regular Google |
|---------|-----------|---------|------------|----------------|
| Authentication | WBG Token | API Key | None | API Key |
| Rate Limits | Organizational | Per API Key | Limited | Per API Key |
| Security | High | Medium | Low | Medium |
| Result Quality | High | High | Medium | High |
| Raw Content | No | Yes | No | Optional |

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

1. **Regenerate Token**:
   ```bash
   rm .wbg_token_cache.bin
   python scripts/generate_token.py
   ```

2. **Check Network Access**: Ensure you can reach:
   - `azapimdev.worldbank.org`
   - `login.microsoftonline.com`

### No Results

If searches return no results:

1. **Check Query**: Ensure query doesn't contain restricted information
2. **Simplify Query**: Try shorter, more general queries
3. **Check Connectivity**: Verify network access to WBG services

### Rate Limiting

The WBG Google Search API may have rate limits. The system includes:
- Automatic retry logic
- Concurrent request limiting
- Proper error handling

## Integration with LLMs

When using WBG models (o4-mini, gpt-4.1) with WBG Google Search, you get:
- Unified authentication (same token for both)
- Optimized for research workflows
- Consistent security standards

## Example Workflow

Here's a complete example using WBG services:

```bash
# 1. Authenticate (once)
python scripts/generate_token.py

# 2. Run report with WBG Google Search and o4-mini
python cli.py --prompt system_prompt.txt --country "Kenya"

# The system will:
# - Use WBG Google Search for web searches
# - Use o4-mini for report generation
# - Handle all authentication automatically
```

## Best Practices

1. **Query Design**: Keep queries focused and specific
2. **Result Count**: Start with 5 results, increase if needed
3. **Error Handling**: The system handles errors gracefully
4. **Security**: Always follow organizational data classification guidelines

## Support

For issues specific to:
- **WBG Google Search API**: Contact the Conversational AI platform team
- **Authentication**: See WBG endpoint documentation
- **Integration**: Check Open Deep Research documentation