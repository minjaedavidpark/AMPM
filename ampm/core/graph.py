"""
Meeting Knowledge Graph
=======================
NetworkX-based knowledge graph for meetings, decisions, and relationships.

The graph connects:
- Meetings → Decisions → Action Items
- People ↔ Decisions (made_by, confirmed_by)
- People ↔ Action Items (assigned_to)
- Topics ↔ Meetings (discussed_in)
- Decisions ↔ Decisions (supersedes, contradicts)
"""

import networkx as nx
from typing import Optional
from datetime import datetime

from ..models import (
    Meeting, Decision, ActionItem, Person, Topic, Blocker,
    Update, Learning, Project, RelationType,
    MeetingType, DecisionStatus, ActionStatus
)


class MeetingGraph:
    """
    Knowledge graph for meeting memory.

    Stores all meeting artifacts and their relationships,
    enabling traversal queries like:
    - "What decisions led to this action item?"
    - "What meetings discussed this topic?"
    - "What's the history of this decision?"
    """

    def __init__(self):
        """Initialize an empty meeting graph."""
        self.graph = nx.DiGraph()
        self._meetings: dict[str, Meeting] = {}
        self._decisions: dict[str, Decision] = {}
        self._action_items: dict[str, ActionItem] = {}
        self._people: dict[str, Person] = {}
        self._topics: dict[str, Topic] = {}
        self._blockers: dict[str, Blocker] = {}
        self._projects: dict[str, Project] = {}

    # ==================== Add Nodes ====================

    def add_meeting(self, meeting: Meeting) -> None:
        """Add a meeting to the graph."""
        self._meetings[meeting.id] = meeting
        self.graph.add_node(
            meeting.id,
            type="meeting",
            title=meeting.title,
            date=meeting.date,
            data=meeting
        )

    def add_decision(self, decision: Decision) -> None:
        """Add a decision to the graph."""
        self._decisions[decision.id] = decision
        self.graph.add_node(
            decision.id,
            type="decision",
            content=decision.content,
            data=decision
        )

        # Link to meeting
        if decision.meeting_id:
            self.graph.add_edge(
                decision.meeting_id,
                decision.id,
                relation=RelationType.CONTAINS_DECISION.value
            )

        # Link to person who made it
        if decision.made_by:
            self.graph.add_edge(
                decision.id,
                decision.made_by,
                relation=RelationType.MADE_BY.value
            )

    def add_action_item(self, action: ActionItem) -> None:
        """Add an action item to the graph."""
        self._action_items[action.id] = action
        self.graph.add_node(
            action.id,
            type="action_item",
            task=action.task,
            data=action
        )

        # Link to meeting
        if action.meeting_id:
            self.graph.add_edge(
                action.meeting_id,
                action.id,
                relation=RelationType.CONTAINS_ACTION.value
            )

        # Link to decision
        if action.decision_id:
            self.graph.add_edge(
                action.id,
                action.decision_id,
                relation=RelationType.FOLLOWS_FROM.value
            )

        # Link to assigned person
        if action.assigned_to:
            self.graph.add_edge(
                action.id,
                action.assigned_to,
                relation=RelationType.ASSIGNED_TO.value
            )

    def add_person(self, person: Person) -> None:
        """Add a person to the graph."""
        self._people[person.id] = person
        self.graph.add_node(
            person.id,
            type="person",
            name=person.name,
            data=person
        )

    def add_topic(self, topic: Topic) -> None:
        """Add a topic to the graph."""
        self._topics[topic.id] = topic
        self.graph.add_node(
            topic.id,
            type="topic",
            name=topic.name,
            data=topic
        )

    # ==================== Query Methods ====================

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID."""
        return self._meetings.get(meeting_id)

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        return self._decisions.get(decision_id)

    def get_person(self, person_id: str) -> Optional[Person]:
        """Get a person by ID."""
        return self._people.get(person_id)

    def get_decisions_by_meeting(self, meeting_id: str) -> list[Decision]:
        """Get all decisions made in a meeting."""
        decisions = []
        for _, target, data in self.graph.out_edges(meeting_id, data=True):
            if data.get("relation") == RelationType.CONTAINS_DECISION.value:
                if target in self._decisions:
                    decisions.append(self._decisions[target])
        return decisions

    def get_decisions_by_person(self, person_id: str) -> list[Decision]:
        """Get all decisions made by a person."""
        decisions = []
        for source, _, data in self.graph.in_edges(person_id, data=True):
            if data.get("relation") == RelationType.MADE_BY.value:
                if source in self._decisions:
                    decisions.append(self._decisions[source])
        return decisions

    def get_decisions_by_topic(self, topic_name: str) -> list[Decision]:
        """Get all decisions about a topic."""
        return [d for d in self._decisions.values()
                if d.topic and topic_name.lower() in d.topic.lower()]

    def get_action_items_by_person(self, person_id: str) -> list[ActionItem]:
        """Get all action items assigned to a person."""
        actions = []
        for source, _, data in self.graph.in_edges(person_id, data=True):
            if data.get("relation") == RelationType.ASSIGNED_TO.value:
                if source in self._action_items:
                    actions.append(self._action_items[source])
        return actions

    def get_action_items_by_decision(self, decision_id: str) -> list[ActionItem]:
        """Get all action items that follow from a decision."""
        actions = []
        for source, _, data in self.graph.in_edges(decision_id, data=True):
            if data.get("relation") == RelationType.FOLLOWS_FROM.value:
                if source in self._action_items:
                    actions.append(self._action_items[source])
        return actions

    def get_meetings_by_topic(self, topic_name: str) -> list[Meeting]:
        """Get all meetings that discussed a topic."""
        meetings = []
        for meeting in self._meetings.values():
            # Check decisions in meeting for topic
            for dec_id in meeting.decisions:
                if dec_id in self._decisions:
                    dec = self._decisions[dec_id]
                    if dec.topic and topic_name.lower() in dec.topic.lower():
                        meetings.append(meeting)
                        break
        return sorted(meetings, key=lambda m: m.date)

    # ==================== Graph Traversal ====================

    def get_downstream(self, node_id: str, depth: int = 3) -> list[str]:
        """
        Get all nodes downstream from a given node.
        Used for ripple detection.
        """
        visited = set()
        to_visit = [(node_id, 0)]
        downstream = []

        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current in visited or current_depth > depth:
                continue

            visited.add(current)
            if current != node_id:
                downstream.append(current)

            # Add all successors
            for successor in self.graph.successors(current):
                if successor not in visited:
                    to_visit.append((successor, current_depth + 1))

        return downstream

    def get_upstream(self, node_id: str, depth: int = 3) -> list[str]:
        """
        Get all nodes upstream from a given node.
        Used for tracing decision origins.
        """
        visited = set()
        to_visit = [(node_id, 0)]
        upstream = []

        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current in visited or current_depth > depth:
                continue

            visited.add(current)
            if current != node_id:
                upstream.append(current)

            # Add all predecessors
            for predecessor in self.graph.predecessors(current):
                if predecessor not in visited:
                    to_visit.append((predecessor, current_depth + 1))

        return upstream

    def get_decision_history(self, topic: str) -> list[dict]:
        """
        Get the full history of decisions on a topic.
        Returns decisions in chronological order with context.
        """
        decisions = self.get_decisions_by_topic(topic)

        history = []
        for decision in sorted(decisions, key=lambda d: d.timestamp):
            meeting = self.get_meeting(decision.meeting_id) if decision.meeting_id else None
            person = self.get_person(decision.made_by) if decision.made_by else None

            history.append({
                "decision": decision,
                "meeting": meeting,
                "made_by": person,
                "date": decision.timestamp,
                "status": decision.status.value
            })

        return history

    # ==================== Statistics ====================

    @property
    def stats(self) -> dict:
        """Get graph statistics."""
        return {
            "meetings": len(self._meetings),
            "decisions": len(self._decisions),
            "action_items": len(self._action_items),
            "people": len(self._people),
            "topics": len(self._topics),
            "blockers": len(self._blockers),
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges()
        }

    def __repr__(self) -> str:
        stats = self.stats
        return (
            f"MeetingGraph("
            f"meetings={stats['meetings']}, "
            f"decisions={stats['decisions']}, "
            f"action_items={stats['action_items']}, "
            f"people={stats['people']})"
        )

    # ==================== Persistence ====================

    def save(self, filepath: str) -> None:
        """
        Save the knowledge graph to a file.
        
        Args:
            filepath: Path to save the graph (JSON format)
        """
        import json
        from pathlib import Path
        
        def serialize_obj(obj):
            """Convert dataclass to dict for JSON serialization."""
            if hasattr(obj, '__dataclass_fields__'):
                result = {}
                for field_name in obj.__dataclass_fields__:
                    value = getattr(obj, field_name)
                    if isinstance(value, datetime):
                        result[field_name] = value.isoformat()
                    elif hasattr(value, 'value'):  # Enum
                        result[field_name] = value.value
                    else:
                        result[field_name] = value
                return result
            return obj
        
        data = {
            "version": "1.0",
            "meetings": {k: serialize_obj(v) for k, v in self._meetings.items()},
            "decisions": {k: serialize_obj(v) for k, v in self._decisions.items()},
            "action_items": {k: serialize_obj(v) for k, v in self._action_items.items()},
            "people": {k: serialize_obj(v) for k, v in self._people.items()},
            "topics": {k: serialize_obj(v) for k, v in self._topics.items()},
            "blockers": {k: serialize_obj(v) for k, v in self._blockers.items()},
            "projects": {k: serialize_obj(v) for k, v in self._projects.items()},
            "graph_nodes": list(self.graph.nodes(data=True)),
            "graph_edges": list(self.graph.edges(data=True))
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Graph saved to {filepath}")

    def load(self, filepath: str) -> bool:
        """
        Load the knowledge graph from a file.
        
        Args:
            filepath: Path to load the graph from
            
        Returns:
            True if loaded successfully, False otherwise
        """
        import json
        from pathlib import Path
        
        if not Path(filepath).exists():
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Clear existing data
            self._meetings.clear()
            self._decisions.clear()
            self._action_items.clear()
            self._people.clear()
            self._topics.clear()
            self._blockers.clear()
            self._projects.clear()
            self.graph.clear()
            
            # Restore people
            for person_id, person_data in data.get("people", {}).items():
                person = Person(
                    id=person_data["id"],
                    name=person_data["name"],
                    role=person_data.get("role"),
                    email=person_data.get("email"),
                    expertise=person_data.get("expertise", [])
                )
                self._people[person_id] = person
            
            # Restore topics
            for topic_id, topic_data in data.get("topics", {}).items():
                topic = Topic(
                    id=topic_data["id"],
                    name=topic_data["name"],
                    description=topic_data.get("description"),
                    tags=topic_data.get("tags", [])
                )
                self._topics[topic_id] = topic
            
            # Restore meetings
            for meeting_id, meeting_data in data.get("meetings", {}).items():
                date = datetime.fromisoformat(meeting_data["date"]) if meeting_data.get("date") else datetime.now()
                meeting_type_str = meeting_data.get("meeting_type", "ad_hoc")
                meeting_type = MeetingType(meeting_type_str) if meeting_type_str else MeetingType.AD_HOC
                
                meeting = Meeting(
                    id=meeting_data["id"],
                    title=meeting_data["title"],
                    date=date,
                    meeting_type=meeting_type,
                    attendees=meeting_data.get("attendees", []),
                    decisions=meeting_data.get("decisions", []),
                    action_items=meeting_data.get("action_items", []),
                    blockers=meeting_data.get("blockers", []),
                    updates=meeting_data.get("updates", []),
                    learnings=meeting_data.get("learnings", []),
                    topics=meeting_data.get("topics", []),
                    transcript=meeting_data.get("transcript"),
                    summary=meeting_data.get("summary"),
                    duration_minutes=meeting_data.get("duration_minutes"),
                    project=meeting_data.get("project")
                )
                self._meetings[meeting_id] = meeting
            
            # Restore decisions
            for decision_id, dec_data in data.get("decisions", {}).items():
                timestamp = datetime.fromisoformat(dec_data["timestamp"]) if dec_data.get("timestamp") else datetime.now()
                status_str = dec_data.get("status", "confirmed")
                status = DecisionStatus(status_str) if status_str else DecisionStatus.CONFIRMED
                
                decision = Decision(
                    id=dec_data["id"],
                    content=dec_data["content"],
                    rationale=dec_data.get("rationale"),
                    topic=dec_data.get("topic"),
                    made_by=dec_data.get("made_by"),
                    confirmed_by=dec_data.get("confirmed_by"),
                    meeting_id=dec_data.get("meeting_id"),
                    quote=dec_data.get("quote"),
                    status=status,
                    confidence=dec_data.get("confidence", 1.0),
                    timestamp=timestamp,
                    superseded_by=dec_data.get("superseded_by")
                )
                self._decisions[decision_id] = decision
            
            # Restore action items
            for action_id, action_data in data.get("action_items", {}).items():
                due_date = datetime.fromisoformat(action_data["due_date"]) if action_data.get("due_date") else None
                created_at = datetime.fromisoformat(action_data["created_at"]) if action_data.get("created_at") else datetime.now()
                completed_at = datetime.fromisoformat(action_data["completed_at"]) if action_data.get("completed_at") else None
                status_str = action_data.get("status", "pending")
                status = ActionStatus(status_str) if status_str else ActionStatus.PENDING
                
                action = ActionItem(
                    id=action_data["id"],
                    task=action_data["task"],
                    assigned_to=action_data.get("assigned_to"),
                    meeting_id=action_data.get("meeting_id"),
                    decision_id=action_data.get("decision_id"),
                    due_date=due_date,
                    status=status,
                    estimated_days=action_data.get("estimated_days"),
                    actual_days=action_data.get("actual_days"),
                    blocker=action_data.get("blocker"),
                    completed_at=completed_at,
                    created_at=created_at
                )
                self._action_items[action_id] = action
            
            # Restore blockers
            for blocker_id, blocker_data in data.get("blockers", {}).items():
                created_at = datetime.fromisoformat(blocker_data["created_at"]) if blocker_data.get("created_at") else datetime.now()
                resolved_at = datetime.fromisoformat(blocker_data["resolved_at"]) if blocker_data.get("resolved_at") else None
                
                blocker = Blocker(
                    id=blocker_data["id"],
                    description=blocker_data["description"],
                    reported_by=blocker_data.get("reported_by"),
                    meeting_id=blocker_data.get("meeting_id"),
                    impact=blocker_data.get("impact"),
                    resolution=blocker_data.get("resolution"),
                    resolved=blocker_data.get("resolved", False),
                    resolved_at=resolved_at,
                    created_at=created_at
                )
                self._blockers[blocker_id] = blocker
            
            # Restore NetworkX graph
            for node_id, node_data in data.get("graph_nodes", []):
                self.graph.add_node(node_id, **node_data)
            
            for source, target, edge_data in data.get("graph_edges", []):
                self.graph.add_edge(source, target, **edge_data)
            
            print(f"Graph loaded from {filepath}: {self.stats}")
            return True
            
        except Exception as e:
            print(f"Error loading graph: {e}")
            return False
