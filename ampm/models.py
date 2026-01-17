"""
AMPM Data Models
================
Core data structures for the meeting memory system.

Node Types:
- Meeting: A recorded meeting with attendees, date, context
- Decision: A decision made in a meeting with rationale
- ActionItem: A task assigned to someone with status
- Person: A team member
- Topic: A discussion topic that spans meetings

Relationships:
- Meeting --[CONTAINS]--> Decision
- Meeting --[CONTAINS]--> ActionItem
- Decision --[MADE_BY]--> Person
- Decision --[ABOUT]--> Topic
- ActionItem --[ASSIGNED_TO]--> Person
- ActionItem --[FOLLOWS_FROM]--> Decision
- Meeting --[ATTENDED_BY]--> Person
- Topic --[DISCUSSED_IN]--> Meeting
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class DecisionStatus(Enum):
    """Status of a decision."""
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"
    REVERSED = "reversed"


class ActionStatus(Enum):
    """Status of an action item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MeetingType(Enum):
    """Type of meeting."""
    STANDUP = "standup"
    SPRINT_PLANNING = "sprint_planning"
    RETROSPECTIVE = "retrospective"
    DESIGN_REVIEW = "design_review"
    STAKEHOLDER_SYNC = "stakeholder_sync"
    ONE_ON_ONE = "one_on_one"
    ALL_HANDS = "all_hands"
    AD_HOC = "ad_hoc"


@dataclass
class Person:
    """A team member."""
    id: str
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    expertise: list[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Topic:
    """A discussion topic that can span multiple meetings."""
    id: str
    name: str
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Decision:
    """A decision made in a meeting."""
    id: str
    content: str  # What was decided
    rationale: Optional[str] = None  # Why it was decided
    topic: Optional[str] = None  # Topic area
    made_by: Optional[str] = None  # Person ID
    confirmed_by: Optional[str] = None  # Person ID
    meeting_id: Optional[str] = None
    quote: Optional[str] = None  # Direct quote from meeting
    status: DecisionStatus = DecisionStatus.CONFIRMED
    confidence: float = 1.0  # 0-1 confidence score
    timestamp: datetime = field(default_factory=datetime.now)
    superseded_by: Optional[str] = None  # Decision ID if superseded

    def __hash__(self):
        return hash(self.id)


@dataclass
class ActionItem:
    """An action item assigned in a meeting."""
    id: str
    task: str
    assigned_to: Optional[str] = None  # Person ID
    meeting_id: Optional[str] = None
    decision_id: Optional[str] = None  # If follows from a decision
    due_date: Optional[datetime] = None
    status: ActionStatus = ActionStatus.PENDING
    estimated_days: Optional[int] = None
    actual_days: Optional[int] = None
    blocker: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Blocker:
    """A blocker reported in a meeting."""
    id: str
    description: str
    reported_by: Optional[str] = None  # Person ID
    meeting_id: Optional[str] = None
    impact: Optional[str] = None
    resolution: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Update:
    """A status update from a person in a meeting."""
    id: str
    person_id: str
    content: str
    meeting_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Learning:
    """A lesson learned captured in a meeting."""
    id: str
    lesson: str
    context: Optional[str] = None
    meeting_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Meeting:
    """A meeting with all its contents."""
    id: str
    title: str
    date: datetime
    meeting_type: MeetingType = MeetingType.AD_HOC
    attendees: list[str] = field(default_factory=list)  # Person IDs
    decisions: list[str] = field(default_factory=list)  # Decision IDs
    action_items: list[str] = field(default_factory=list)  # ActionItem IDs
    blockers: list[str] = field(default_factory=list)  # Blocker IDs
    updates: list[str] = field(default_factory=list)  # Update IDs
    learnings: list[str] = field(default_factory=list)  # Learning IDs
    topics: list[str] = field(default_factory=list)  # Topic IDs
    transcript: Optional[str] = None
    summary: Optional[str] = None
    duration_minutes: Optional[int] = None
    project: Optional[str] = None

    def __hash__(self):
        return hash(self.id)


@dataclass
class Project:
    """A project that meetings belong to."""
    id: str
    name: str
    description: Optional[str] = None
    team: list[str] = field(default_factory=list)  # Person IDs
    meetings: list[str] = field(default_factory=list)  # Meeting IDs
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)


# Relationship types for the knowledge graph
class RelationType(Enum):
    """Types of relationships in the knowledge graph."""
    # Meeting relationships
    CONTAINS_DECISION = "contains_decision"
    CONTAINS_ACTION = "contains_action"
    CONTAINS_BLOCKER = "contains_blocker"
    ATTENDED_BY = "attended_by"
    DISCUSSES_TOPIC = "discusses_topic"

    # Decision relationships
    MADE_BY = "made_by"
    CONFIRMED_BY = "confirmed_by"
    ABOUT_TOPIC = "about_topic"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"

    # Action item relationships
    ASSIGNED_TO = "assigned_to"
    FOLLOWS_FROM = "follows_from"
    BLOCKED_BY = "blocked_by"

    # Cross-meeting relationships
    RELATED_TO = "related_to"
    REFERENCES = "references"
    CONTINUES_FROM = "continues_from"
