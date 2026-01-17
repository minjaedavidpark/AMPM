"""
AMPM Interfaces
===============
User interfaces for interacting with meeting memory.

Interfaces:
- VoiceBot: Local voice bot (mic → STT → LLM → TTS → speaker)
- MeetBot: Google Meet bot with live audio
- DemoMeetBot: Google Meet bot with typed questions
"""

from .voice_bot import VoiceBot
from .meet_bot import MeetBot, DemoMeetBot

__all__ = ["VoiceBot", "MeetBot", "DemoMeetBot"]
