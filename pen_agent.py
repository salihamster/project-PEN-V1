"""
PEN Agent - Entry Point for Interactive CLI

This module provides the interactive CLI interface for the PEN Agent.
It wraps the core PENAgent from src.agent.agent and provides a user-friendly
command-line interface.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load .env
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.agent import PENAgent
from src.utils.logger import get_logger

# Logger setup
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"pen_agent_{datetime.now().strftime('%Y-%m-%d')}.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# ============================================================================
# Interactive Chat
# ============================================================================

def interactive_chat():
    """Interactive chat mode."""
    print("\n" + "="*70)
    print("🤖 PEN - Personal Assistant")
    print("="*70)
    print("\nPowered by Google Gemini 2.5 Flash (Latest, fast, and powerful model)")
    print("Commands: 'exit' (quit), 'reset' (reset conversation), 'help' (help)")
    print("="*70)
    
    # Get API key from .env
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY environment variable is not set")
        print("💡 Add to .env file: GEMINI_API_KEY=...")
        return
    
    # Minimax API key (for L4)
    minimax_api_key = os.getenv("MINIMAX_API_KEY")
    
    # Create agent
    try:
        agent = PENAgent(api_key, minimax_api_key)
        agent.session_source = "cli"  # Set session source
    except Exception as e:
        print(f"\n❌ Failed to start agent: {e}")
        logger.error(f"Agent initialization error: {e}", exc_info=True)
        return
    
    print("\n✅ Agent ready! You can ask questions.\n")
    
    while True:
        try:
            # User input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Commands
            if user_input.lower() == "exit":
                # If session exists, sleep first (L4 update happens in sleep)
                if agent.messages:
                    print("\n💤 Archiving session...")
                    agent.sleep()
                    print("✅ Session archived.")
                
                print("\n👋 Goodbye!")
                break
            
            elif user_input.lower() == "reset":
                agent.reset()
                print("\n🔄 Conversation reset.\n")
                continue

            elif user_input.lower() == "sleep":
                print("\n💤 Starting sleep cycle...")
                agent.sleep()
                print("✅ Session archived, new session started.\n")
                continue
            
            elif user_input.lower() == "help":
                print("""
📚 Help:

Example questions:
• "How many chats do I have?"
• "What happened in the last 3 days?"
• "Search for the word homework"
• "Show me the vitaminsizler chat"
• "What files are in Drive?"
• "Show statistics"

Commands:
• exit - Quit
• reset - Reset conversation
• sleep - Archive session and start new
• help - This help message
                """)
                continue
            
            # Ask agent
            print("\n🤖 PEN: ", end="", flush=True)
            response = agent.chat(user_message=user_input)
            print(response + "\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            logger.error(f"Chat error: {e}", exc_info=True)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    interactive_chat()
