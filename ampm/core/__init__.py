"""
AMPM Core - Memory System
=========================
The core memory layer for meeting intelligence.

Components:
- graph: Knowledge graph for meetings, decisions, and relationships
- embeddings: Vector embeddings for semantic search
- query: Context retrieval ("Why did we decide X?")
- ripple: Change impact detection
"""

from .graph import MeetingGraph
from .query import QueryEngine
from .ripple import RippleDetector

__all__ = ["MeetingGraph", "QueryEngine", "RippleDetector"]
