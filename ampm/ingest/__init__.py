"""
AMPM Ingest
===========
Data ingestion for meeting memory.

Components:
- MeetingLoader: Load meeting data from JSON files
"""

from .loader import MeetingLoader

__all__ = ["MeetingLoader"]
