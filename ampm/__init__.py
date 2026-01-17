"""
AMPM - AI Meeting Product Manager
=================================
A contextual memory layer for meetings.

"From AM to PM, Never Miss a Decision"

Core Components:
- MeetingGraph: Knowledge graph for meetings, decisions, relationships
- QueryEngine: Natural language queries ("Why did we decide X?")
- RippleDetector: Change impact detection
- EmbeddingStore: Semantic search (integrates with Backboard API)

Agents:
- MeetingAgent: Extract decisions from meeting data
- DecisionAgent: Track decision history and conflicts
- ActionAgent: Monitor action items and blockers

Interfaces:
- VoiceBot: Local voice assistant
- MeetBot: Google Meet bot (live audio)
- DemoMeetBot: Google Meet bot (typed questions)

Usage:
    from ampm import MeetingGraph, QueryEngine, MeetingLoader

    # Load meeting data
    loader = MeetingLoader()
    loader.load_sample_data()

    # Query the memory
    engine = QueryEngine(loader.graph)
    result = engine.query("Why did we choose Stripe?")
    print(result.answer)
"""

__version__ = "0.2.0"
__author__ = "AMPM Team"

# Core memory system
from .core import MeetingGraph, QueryEngine, RippleDetector

# Data ingestion
from .ingest import MeetingLoader

# Agents
from .agents import MeetingAgent, DecisionAgent, ActionAgent

# Interfaces (optional - require sounddevice, elevenlabs, etc.)
try:
    from .interfaces import VoiceBot, MeetBot, DemoMeetBot
    AMPMBot = VoiceBot  # Backward compatibility alias
except ImportError:
    VoiceBot = None
    MeetBot = None
    DemoMeetBot = None
    AMPMBot = None

# Models
from .models import (
    Meeting, Decision, ActionItem, Person, Topic,
    Blocker, Update, Learning, Project,
    DecisionStatus, ActionStatus, MeetingType
)

# Backward compatibility aliases
MeetingKnowledge = MeetingLoader  # Legacy alias

__all__ = [
    # Core
    "MeetingGraph",
    "QueryEngine",
    "RippleDetector",

    # Ingest
    "MeetingLoader",

    # Agents
    "MeetingAgent",
    "DecisionAgent",
    "ActionAgent",

    # Interfaces
    "VoiceBot",
    "MeetBot",
    "DemoMeetBot",

    # Models
    "Meeting",
    "Decision",
    "ActionItem",
    "Person",
    "Topic",
    "Blocker",
    "Update",
    "Learning",
    "Project",
    "DecisionStatus",
    "ActionStatus",
    "MeetingType",

    # Aliases
    "AMPMBot",
    "MeetingKnowledge",
]
