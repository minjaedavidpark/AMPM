"""
Meeting Data Loader
===================
Load meeting data from various sources into the memory system.
"""

import json
from pathlib import Path
from typing import Optional, Union

from ..core.graph import MeetingGraph
from ..core.embeddings import EmbeddingStore
from ..agents.meeting_agent import MeetingAgent
from ..models import Meeting


class MeetingLoader:
    """
    Load meeting data from files into the knowledge graph.

    Supports:
    - Single meeting JSON files
    - Multi-meeting JSON files (array or with "meetings" key)
    - Directory of meeting files
    """

    def __init__(self, graph: Optional[MeetingGraph] = None,
                 embeddings: Optional[EmbeddingStore] = None):
        """
        Initialize the meeting loader.

        Args:
            graph: Optional existing graph (creates new if None)
            embeddings: Optional embedding store for indexing
        """
        self.graph = graph or MeetingGraph()
        self.embeddings = embeddings or EmbeddingStore(use_backboard=True)
        self.agent = MeetingAgent(self.graph, self.embeddings)

    def load_file(self, path: Union[str, Path]) -> list[Meeting]:
        """
        Load meetings from a JSON file.

        Args:
            path: Path to JSON file

        Returns:
            List of loaded Meeting objects
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        return self._process_data(data)

    def load_directory(self, path: Union[str, Path],
                       pattern: str = "*.json") -> list[Meeting]:
        """
        Load all meeting files from a directory.

        Args:
            path: Directory path
            pattern: Glob pattern for files (default: *.json)

        Returns:
            List of all loaded Meeting objects
        """
        path = Path(path)

        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        meetings = []
        for file_path in sorted(path.glob(pattern)):
            try:
                file_meetings = self.load_file(file_path)
                meetings.extend(file_meetings)
                print(f"Loaded {len(file_meetings)} meeting(s) from {file_path.name}")
            except Exception as e:
                print(f"Error loading {file_path.name}: {e}")

        return meetings

    def _process_data(self, data: Union[dict, list]) -> list[Meeting]:
        """Process JSON data and return meetings."""
        meetings = []

        # Handle different formats
        if isinstance(data, list):
            # Array of meetings
            for item in data:
                meeting = self.agent.process_meeting_data(item)
                meetings.append(meeting)

        elif isinstance(data, dict):
            if "meetings" in data:
                # Format: {"project": "...", "team": {...}, "meetings": [...]}
                # Store project/team info
                project_name = data.get("project")
                team = data.get("team", {})

                # Add team members
                for name, role in team.items():
                    from ..models import Person
                    person_id = name.lower().replace(" ", "_")
                    if not self.graph.get_person(person_id):
                        person = Person(id=person_id, name=name, role=role)
                        self.graph.add_person(person)

                # Process meetings
                for item in data["meetings"]:
                    item["project"] = project_name
                    meeting = self.agent.process_meeting_data(item)
                    meetings.append(meeting)

            else:
                # Single meeting
                meeting = self.agent.process_meeting_data(data)
                meetings.append(meeting)

        return meetings

    def load_sample_data(self) -> list[Meeting]:
        """
        Load the default sample meeting data.

        Returns:
            List of sample Meeting objects
        """
        # Find sample data file
        package_dir = Path(__file__).parent.parent.parent
        sample_path = package_dir / "data" / "sample_meetings.json"

        if not sample_path.exists():
            # Try alternate location
            sample_path = package_dir / "data" / "samples"
            if sample_path.is_dir():
                return self.load_directory(sample_path)

            raise FileNotFoundError("Sample data not found")

        return self.load_file(sample_path)

    def get_context_for_query(self) -> str:
        """
        Get formatted context for LLM queries.

        This provides backward compatibility with the old MeetingKnowledge class.
        """
        parts = []

        # Get all meetings sorted by date
        meetings = sorted(
            self.graph._meetings.values(),
            key=lambda m: m.date
        )

        if not meetings:
            return "No meeting data loaded."

        parts.append("=== MEETING HISTORY ===")

        for meeting in meetings:
            parts.append(f"\n--- {meeting.title} ({meeting.date.strftime('%Y-%m-%d')}) ---")

            if meeting.attendees:
                attendee_names = []
                for pid in meeting.attendees:
                    person = self.graph.get_person(pid)
                    if person:
                        attendee_names.append(person.name)
                parts.append(f"Attendees: {', '.join(attendee_names)}")

            # Decisions
            for dec_id in meeting.decisions:
                dec = self.graph.get_decision(dec_id)
                if dec:
                    parts.append(f"\nDECISION: {dec.content}")
                    if dec.topic:
                        parts.append(f"  Topic: {dec.topic}")
                    if dec.rationale:
                        parts.append(f"  Reasoning: {dec.rationale}")
                    if dec.made_by:
                        person = self.graph.get_person(dec.made_by)
                        if person:
                            parts.append(f"  Made by: {person.name}")
                    if dec.quote:
                        parts.append(f"  Quote: \"{dec.quote}\"")

            # Action items
            for action_id in meeting.action_items:
                action = self.graph._action_items.get(action_id)
                if action:
                    parts.append(f"\nACTION ITEM: {action.task}")
                    if action.assigned_to:
                        person = self.graph.get_person(action.assigned_to)
                        if person:
                            parts.append(f"  Assigned to: {person.name}")
                    if action.due_date:
                        parts.append(f"  Due: {action.due_date.strftime('%Y-%m-%d')}")
                    parts.append(f"  Status: {action.status.value}")

            # Blockers
            for blocker_id in meeting.blockers:
                blocker = self.graph._blockers.get(blocker_id)
                if blocker:
                    parts.append(f"\nBLOCKER: {blocker.description}")
                    if blocker.reported_by:
                        person = self.graph.get_person(blocker.reported_by)
                        if person:
                            parts.append(f"  Reported by: {person.name}")
                    if blocker.impact:
                        parts.append(f"  Impact: {blocker.impact}")

        return "\n".join(parts)

    @property
    def stats(self) -> dict:
        """Get statistics about loaded data."""
        return {
            **self.graph.stats,
            "indexed_documents": self.embeddings.document_count
        }
