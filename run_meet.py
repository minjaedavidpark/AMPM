#!/usr/bin/env python3
"""
AMPM Google Meet Bot
====================
Join a Google Meet and answer questions.

Usage:
    # Demo mode (type questions in terminal):
    python run_meet.py <meeting_url>

    # Live audio mode (requires virtual audio routing):
    python run_meet.py <meeting_url> --live

Example:
    python run_meet.py "https://meet.google.com/abc-defg-hij"
"""

import os
import sys
import asyncio

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from ampm import DemoMeetBot, MeetBot


def print_banner():
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
    ║         Google Meet Bot                                   ║
    ║         AI Meeting Assistant                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def print_usage():
    print("Usage:")
    print("  python run_meet.py <meeting_url>          # Demo mode (type questions)")
    print("  python run_meet.py <meeting_url> --live   # Live audio mode")
    print("")
    print("Example:")
    print("  python run_meet.py 'https://meet.google.com/abc-defg-hij'")


async def run_demo(meeting_url: str):
    """Run in demo mode - type questions."""
    bot = DemoMeetBot(meeting_url)
    await bot.start()


async def run_live(meeting_url: str):
    """Run in live audio mode."""
    bot = MeetBot(meeting_url)
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n\nLeaving meeting...")
    finally:
        await bot.cleanup()
        print("Goodbye!")


def main():
    """Entry point for Google Meet bot."""
    print_banner()

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    meeting_url = sys.argv[1]

    # Check for --live flag
    live_mode = "--live" in sys.argv

    # Validate URL
    if not meeting_url.startswith("https://meet.google.com/"):
        print("Error: Invalid Google Meet URL")
        print("URL should look like: https://meet.google.com/abc-defg-hij")
        sys.exit(1)

    # Check API keys
    required_keys = ["CEREBRAS_API_KEY", "ELEVENLABS_API_KEY"]
    if live_mode:
        required_keys.append("OPENAI_API_KEY")

    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"Error: Missing API keys: {', '.join(missing)}")
        print("\nSetup:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your API keys to .env")
        sys.exit(1)

    # Run
    if live_mode:
        print("Mode: LIVE AUDIO")
        print("Note: Requires virtual audio routing (e.g., BlackHole on macOS)")
        asyncio.run(run_live(meeting_url))
    else:
        print("Mode: DEMO (type questions in terminal)")
        asyncio.run(run_demo(meeting_url))


if __name__ == "__main__":
    main()
