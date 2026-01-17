"""
AMPM - AI Meeting Product Manager
=================================
A voice-activated AI assistant that answers questions about meeting history.

Usage:
    from ampm import AMPMBot, MeetingKnowledge, MeetBot
"""

__version__ = "0.1.0"
__author__ = "AMPM Team"

from .knowledge import MeetingKnowledge
from .bot import AMPMBot
from .meet_bot import MeetBot, DemoMeetBot

__all__ = ["AMPMBot", "MeetingKnowledge", "MeetBot", "DemoMeetBot"]
