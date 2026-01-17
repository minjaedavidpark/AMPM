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
    Update, Learning, Project, RelationType
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
