# Migration Guide

This guide explains the changes made to Open Deep Research based on the code review recommendations and how to migrate your existing configurations.

## Overview of Changes

### 1. **Unified Authentication System**
- **Before**: WBG models created their own `WBGAuthManager` internally, ignoring `api_keys` configuration
- **After**: WBG models now accept an `auth_manager` parameter for consistent authentication handling
- **Impact**: No user-facing changes, but authentication is now more predictable

### 2. **Expanded Multi-Agent Search Support**
- **Before**: Multi-agent only supported Tavily, DuckDuckGo, and WBG Google
- **After**: All search APIs are now supported in multi-agent mode (Perplexity, Exa, ArXiv, PubMed, Linkup, Google Search)
- **Migration**: You can now use any search API with `--agent-type multi-agent`

### 3. **CLI Agent Type Selection**
- **Before**: CLI only ran multi-agent implementation
- **After**: New `--agent-type` flag allows choosing between `multi-agent` and `graph` implementations
- **Migration**: 
  ```bash
  # Old way (implicit multi-agent)
  odr --prompt prompt.txt --country "Angola"
  
  # New way (explicit choice)
  odr --prompt prompt.txt --country "Angola" --agent-type multi-agent
  odr --prompt prompt.txt --country "Angola" --agent-type graph
  ```

### 4. **Configuration Format Standardization**
- **Before**: 
  - Multi-agent used: `supervisor_model: "wbg:o4-mini"`
  - Graph-based used: `planner_provider: "wbg"` and `planner_model: "o4-mini"`
- **After**: Both now use the unified `provider:model` format
- **Migration**: Update your configuration files:
  ```yaml
  # Old graph-based configuration
  planner_provider: "wbg"
  planner_model: "o4-mini"
  
  # New unified configuration
  planner_model: "wbg:o4-mini"
  ```

### 5. **Default Models Changed**
- **Before**: Defaults were WBG models (`wbg:o4-mini`)
- **After**: Defaults are now OpenAI models (`openai:gpt-4o`)
- **Migration**: To use WBG models, either:
  - Set `use_wbg_models: true` in your configuration
  - Use the example WBG configuration: `examples/config.wbg.yaml`
  - Set environment variable: `USE_WBG_MODELS=true`

### 6. **Configuration Files**
- **Before**: Hardcoded WBG defaults in source code
- **After**: Example configurations in `examples/` directory
- **Migration**: Copy and customize example configurations:
  ```bash
  cp examples/config.default.yaml my-config.yaml
  # or for WBG users:
  cp examples/config.wbg.yaml my-config.yaml
  ```

## Step-by-Step Migration

### For WBG Users

1. **Update your environment**:
   ```bash
   export USE_WBG_MODELS=true
   ```

2. **Or use configuration file**:
   ```yaml
   # config.yaml
   use_wbg_models: true
   wbg_max_tokens: 100000
   ```

3. **Generate authentication token** (as before):
   ```bash
   python scripts/generate_token.py
   ```

### For Open-Source Users

1. **Set up API keys**:
   ```bash
   cp examples/.env.example .env
   # Edit .env with your API keys
   ```

2. **Choose your models**:
   ```yaml
   # config.yaml
   planner_model: "openai:gpt-4o"  # or "anthropic:claude-3-sonnet"
   writer_model: "openai:gpt-4o"
   search_api: "tavily"  # or any supported API
   ```

3. **Run with your preferred implementation**:
   ```bash
   odr --prompt prompt.txt --country "Angola" --agent-type graph
   ```

## Breaking Changes

1. **Removed `workflow/` directory**: If you were importing from `open_deep_research.workflow`, update imports to use the main modules
2. **CLI wrapper removed**: Use `odr` command directly (installed via pip) instead of `python cli.py`
3. **Configuration field removal**: `planner_provider` and `writer_provider` fields no longer exist in `WorkflowConfiguration`

## New Features

1. **`use_wbg_models` flag**: Automatically configures all models to use WBG endpoints
2. **Unified search API support**: All search APIs now work with both implementations
3. **Example configurations**: Ready-to-use configuration templates in `examples/`
4. **Agent type selection**: Choose implementation via CLI flag

## Troubleshooting

### "Unknown search API" error in multi-agent mode
- **Cause**: Using old version where multi-agent didn't support all search APIs
- **Fix**: Update to latest version with expanded search support

### Models not using WBG endpoints
- **Cause**: `use_wbg_models` not set or old configuration format
- **Fix**: Set `use_wbg_models: true` or update model strings to `"wbg:o4-mini"`

### Import errors from workflow module
- **Cause**: Duplicate workflow directory was removed
- **Fix**: Update imports to use main modules (e.g., `from open_deep_research.configuration import WorkflowConfiguration`)

## Support

For additional help with migration:
- Check the updated README.md
- Review example configurations in `examples/`
- Report issues at: https://github.com/anthropics/open-deep-research/issues