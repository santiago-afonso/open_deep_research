# CLI implementation

This document explains the motivation for adding a command line interface and how the new functionality works.

The repository originally relied on LangGraph Studio running locally to provide a web UI. To make the research tool more flexible, the codebase now exposes a simple `run_multi_agent` helper and a CLI command named `odr`.

`run_multi_agent` can be imported from the `open_deep_research` package. It accepts the human prompt and an optional `auto_accept_plan` flag. When called, it runs the multi-agent workflow and returns the final report.

## CLI Features

The `odr` CLI provides the following functionality:

1. **Template-based prompts**: Use `{countryname}` placeholders in your prompts
2. **Country-specific reports**: Generate reports for any country by passing `--country`
3. **File output**: Reports are saved to `Output/Reports/` with standardized naming
4. **Flexible paths**: Support for custom input/output directories

### Basic Usage

```bash
# Using the wrapper script
python cli.py --prompt system_prompt.txt --country "Angola"

# Using the installed command
odr --prompt system_prompt.txt --country "Angola"
```

### Advanced Options

- `--auto-accept-plan`: Bypasses the plan confirmation step
- `--input-dir`: Override default input directory (default: `Inputs/`)
- `--output-dir`: Override default output directory (default: `Output/Reports/`)

### Output

Reports are saved as `{country}_Tax_Expenditure_Report.md` in the output directory.

## Implementation Details

The CLI is registered as an entry point in `pyproject.toml`, allowing installation of the package with `pip install -e .` and subsequent invocation of `odr` from anywhere.

A wrapper script `cli.py` is provided in the root directory for convenience, allowing users to run `python cli.py` without installing the package.

## Environment Variables

API credentials must be provided as environment variables:
- LLM providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.
- Search APIs: `TAVILY_API_KEY`, `GOOGLE_CX`, etc.

See the authentication documentation for details on API key management.
