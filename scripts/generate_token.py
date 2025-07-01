#!/usr/bin/env python3
"""
Generate and cache authentication token for WBG API access.

This script performs interactive authentication with Microsoft Entra ID
and saves a refresh token that can be used for up to 90 days.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.open_deep_research.wbg_auth_manager import WBGAuthManager


def main():
    print("=== WBG API Token Generation ===")
    print("This will authenticate you with Microsoft Entra ID")
    print("and save a token for future use.\n")
    
    try:
        auth = WBGAuthManager()
        token = auth.get_bearer_token()
        print("\n✅ Token acquired and cached successfully!")
        print(f"Cache location: {auth.token_file}")
        print("\nYou can now run your application scripts.")
        print("The token will automatically refresh for up to 90 days.")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()