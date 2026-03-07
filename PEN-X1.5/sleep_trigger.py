#!/usr/bin/env python3
"""
Sleep Cycle Trigger Script

This script manually triggers the sleep cycle for testing purposes.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.agent import PENAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Trigger sleep cycle."""
    print("🔄 Triggering sleep cycle...")

    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return

    # Minimax API key (optional)
    minimax_api_key = os.getenv("MINIMAX_API_KEY")

    try:
        # Create agent
        agent = PENAgent(api_key, minimax_api_key)
        print("✅ Agent initialized")

        # Trigger sleep
        agent.sleep()
        print("✅ Sleep cycle completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Sleep trigger error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
