#!/usr/bin/env python3
"""
AMPM - AI Meeting Product Manager
=================================
Run the local voice bot (microphone + speakers).

Usage:
    python run.py

Say "Hey Parrot" followed by your question.
"""

import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from ampm import VoiceBot


def main():
    """Entry point for local voice bot."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ███╗   ███╗██████╗ ███╗   ███╗                ║
    ║    ██╔══██╗████╗ ████║██╔══██╗████╗ ████║                ║
    ║    ███████║██╔████╔██║██████╔╝██╔████╔██║                ║
    ║    ██╔══██║██║╚██╔╝██║██╔═══╝ ██║╚██╔╝██║                ║
    ║    ██║  ██║██║ ╚═╝ ██║██║     ██║ ╚═╝ ██║                ║
    ║    ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝     ╚═╝                ║
    ║                                                           ║
    ║         AI Meeting Product Manager                        ║
    ║         From AM to PM, Never Miss a Decision              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        bot = VoiceBot()
        bot.run()
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("\nSetup:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your API keys to .env")
        print("  3. Run: python run.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
