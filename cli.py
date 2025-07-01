#!/usr/bin/env python3
"""
Wrapper script to run the Open Deep Research CLI.

This allows running the tool as:
    python cli.py --prompt system_prompt.txt --country "Angola"

Instead of having to use the installed command:
    odr --prompt system_prompt.txt --country "Angola"
"""

import sys
from open_deep_research.cli import main

if __name__ == "__main__":
    main()