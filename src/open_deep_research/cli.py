"""Command line interface for Open Deep Research."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rich.console import Console

from .agent import run_multi_agent, run_workflow


def main() -> None:
    """Entry point for the ``odr`` command."""
    parser = argparse.ArgumentParser(
        description="Run Open Deep Research to generate country-specific reports"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Path to the system prompt file (e.g., Inputs/system_prompt.txt)",
    )
    parser.add_argument(
        "--country",
        type=str,
        required=True,
        help="Country name to substitute in the prompt",
    )
    parser.add_argument(
        "--auto-accept-plan",
        action="store_true",
        help="Automatically accept the generated plan without confirmation",
    )
    parser.add_argument(
        "--agent-type",
        type=str,
        choices=["multi-agent", "graph"],
        default="multi-agent",
        help="Choose the implementation type: multi-agent (default) or graph-based workflow",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="Inputs",
        help="Directory containing prompt files (default: Inputs)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="Output/Reports",
        help="Directory to save reports (default: Output/Reports)",
    )
    args = parser.parse_args()

    console = Console()
    
    try:
        # Ensure directories exist
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the prompt file
        prompt_path = Path(args.prompt)
        if not prompt_path.is_absolute():
            # If relative path, check in input directory first
            if (input_dir / prompt_path).exists():
                prompt_path = input_dir / prompt_path
        
        if not prompt_path.exists():
            console.print(f"[red]Error: Prompt file not found: {prompt_path}[/red]")
            sys.exit(1)
        
        prompt_template = prompt_path.read_text()
        
        # Replace country placeholder (case-insensitive)
        # Supports {countryname}, {CountryName}, {COUNTRYNAME}, etc.
        prompt = re.sub(
            r'\{countryname\}',
            args.country,
            prompt_template,
            flags=re.IGNORECASE
        )
        
        # Check if substitution was made
        if prompt == prompt_template and '{' in prompt_template:
            console.print(
                "[yellow]Warning: No {countryname} placeholder found in prompt. "
                "The prompt may not have been customized for the country.[/yellow]"
            )
        
        # Generate the report
        console.print(f"[blue]Generating report for {args.country} using {args.agent_type} implementation...[/blue]")
        
        if args.agent_type == "multi-agent":
            report = run_multi_agent(prompt, auto_accept_plan=args.auto_accept_plan)
        else:  # graph
            report = run_workflow(prompt, auto_accept_plan=args.auto_accept_plan)
        
        if not report:
            console.print("[red]Error: No report was generated.[/red]")
            sys.exit(1)
        
        # Save the report
        output_filename = f"{args.country}_Tax_Expenditure_Report.md"
        output_path = output_dir / output_filename
        
        output_path.write_text(report)
        
        console.print(
            f"[green]✓ Report successfully generated and saved to:[/green]\n"
            f"  {output_path}"
        )
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
