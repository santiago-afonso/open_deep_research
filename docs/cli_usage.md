# CLI Usage Guide

This guide explains how to use the Open Deep Research CLI to generate country-specific reports.

## Basic Usage

The CLI can be invoked in two ways:

### Method 1: Using the wrapper script
```bash
python cli.py --prompt system_prompt.txt --country "Angola"
```

### Method 2: Using the installed command
```bash
odr --prompt system_prompt.txt --country "Angola"
```

## Command Line Arguments

### Required Arguments

- `--prompt`: Path to the system prompt file containing the template
  - Can be an absolute path or relative to the current directory
  - If just a filename is provided, it will look in the `Inputs/` directory
  
- `--country`: The country name to substitute in the prompt template
  - This replaces all occurrences of `{countryname}` in the prompt

### Optional Arguments

- `--auto-accept-plan`: Skip the plan confirmation step for faster execution
- `--input-dir`: Override the default input directory (default: `Inputs`)
- `--output-dir`: Override the default output directory (default: `Output/Reports`)

## Directory Structure

The CLI expects and creates the following directory structure:

```
open_deep_research/
├── Inputs/                  # Default location for prompt files
│   └── system_prompt.txt    # Your prompt template
├── Output/                  
│   └── Reports/            # Generated reports are saved here
│       └── Angola_Tax_Expenditure_Report.md
└── cli.py                  # Wrapper script
```

## Prompt Template

Your prompt file should contain `{countryname}` placeholders that will be replaced with the country name:

```
Generate a comprehensive tax expenditure report for {countryname}.

The report should analyze {countryname}'s tax system...
```

## Examples

### Basic usage with default directories:
```bash
python cli.py --prompt system_prompt.txt --country "Angola"
```

### Using auto-accept for faster execution:
```bash
python cli.py --prompt system_prompt.txt --country "Brazil" --auto-accept-plan
```

### Using custom directories:
```bash
python cli.py --prompt custom_prompts/tax_prompt.txt --country "Canada" \
  --input-dir custom_prompts --output-dir results
```

### Using absolute path for prompt:
```bash
python cli.py --prompt /path/to/my/prompt.txt --country "Denmark"
```

## Output

The generated report will be saved as:
```
Output/Reports/{country}_Tax_Expenditure_Report.md
```

For example, if you run with `--country "Angola"`, the output will be:
```
Output/Reports/Angola_Tax_Expenditure_Report.md
```

## Error Handling

The CLI will display helpful error messages for common issues:
- Missing prompt file
- Missing country argument
- Failed report generation
- Directory creation errors

## Tips

1. **Prompt Design**: Make sure your prompt template uses `{countryname}` (case-insensitive) where you want the country name to appear.

2. **Country Names**: Use the full country name in quotes if it contains spaces:
   ```bash
   python cli.py --prompt system_prompt.txt --country "United States"
   ```

3. **Multiple Reports**: You can generate reports for multiple countries by running the command multiple times:
   ```bash
   for country in "Angola" "Brazil" "Canada"; do
     python cli.py --prompt system_prompt.txt --country "$country" --auto-accept-plan
   done
   ```