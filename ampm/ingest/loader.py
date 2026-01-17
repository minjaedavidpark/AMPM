"""
Meeting Data Loader
===================
Load meeting data from various sources into the memory system.

Supports real-time updates during meetings with auto-persistence.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Callable

from ..core.graph import MeetingGraph
from ..core.embeddings import EmbeddingStore
from ..agents.meeting_agent import MeetingAgent
from ..models import (
    Meeting, Decision, ActionItem, Blocker, Person,
    DecisionStatus, ActionStatus, MeetingType
)


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

    # ==================== Real-time Updates ====================

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _auto_save(self, cache_dir: str = ".ampm_cache") -> None:
        """Auto-save graph and embeddings after updates."""
        cache_path = Path(cache_dir)
        cache_path.mkdir(exist_ok=True)
        
        try:
            self.graph.save(str(cache_path / "graph.json"))
            self.embeddings.save(str(cache_path / "embeddings.json"))
        except Exception as e:
            print(f"Auto-save warning: {e}")

    def get_or_create_live_meeting(self, title: str = None) -> Meeting:
        """
        Get or create a 'live' meeting for real-time updates.
        
        Args:
            title: Optional meeting title (defaults to "Live Meeting - {date}")
            
        Returns:
            Meeting object for the current session
        """
        live_meeting_id = "live_meeting"
        
        # Check if live meeting already exists
        existing = self.graph.get_meeting(live_meeting_id)
        if existing:
            return existing
        
        # Create new live meeting
        if not title:
            title = f"Live Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        meeting = Meeting(
            id=live_meeting_id,
            title=title,
            date=datetime.now(),
            meeting_type=MeetingType.AD_HOC,
            attendees=[],
            decisions=[],
            action_items=[],
            blockers=[],
            updates=[],
            learnings=[],
            topics=[]
        )
        
        self.graph.add_meeting(meeting)
        return meeting

    def add_decision_realtime(
        self,
        content: str,
        rationale: str = None,
        topic: str = None,
        made_by: str = None,
        meeting_id: str = "live_meeting",
        auto_save: bool = True
    ) -> Decision:
        """
        Add a decision in real-time during a meeting.
        
        Args:
            content: The decision text
            rationale: Why this decision was made
            topic: Topic area (e.g., "payments", "security")
            made_by: Person ID who made the decision
            meeting_id: Meeting to attach to (defaults to live meeting)
            auto_save: Whether to persist immediately
            
        Returns:
            The created Decision object
        """
        # Ensure meeting exists
        if meeting_id == "live_meeting":
            self.get_or_create_live_meeting()
        
        # Create decision
        decision_id = self._generate_id("dec")
        decision = Decision(
            id=decision_id,
            content=content,
            rationale=rationale,
            topic=topic,
            made_by=made_by,
            meeting_id=meeting_id,
            status=DecisionStatus.CONFIRMED,
            confidence=1.0,
            timestamp=datetime.now()
        )
        
        # Add to graph
        self.graph.add_decision(decision)
        
        # Update meeting's decision list
        meeting = self.graph.get_meeting(meeting_id)
        if meeting and decision_id not in meeting.decisions:
            meeting.decisions.append(decision_id)
        
        # Index in embeddings
        embed_text = f"Decision: {content}"
        if rationale:
            embed_text += f"\nRationale: {rationale}"
        self.embeddings.add_document(
            doc_id=decision_id,
            content=embed_text,
            metadata={
                "type": "decision",
                "topic": topic or "",
                "meeting_id": meeting_id,
                "source": "realtime"
            }
        )
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Added decision: {content[:50]}...")
        return decision

    def add_action_realtime(
        self,
        task: str,
        assigned_to: str = None,
        due_date: datetime = None,
        decision_id: str = None,
        meeting_id: str = "live_meeting",
        auto_save: bool = True
    ) -> ActionItem:
        """
        Add an action item in real-time during a meeting.
        
        Args:
            task: The action item description
            assigned_to: Person ID responsible
            due_date: When it's due
            decision_id: Optional decision this follows from
            meeting_id: Meeting to attach to
            auto_save: Whether to persist immediately
            
        Returns:
            The created ActionItem object
        """
        # Ensure meeting exists
        if meeting_id == "live_meeting":
            self.get_or_create_live_meeting()
        
        # Create action item
        action_id = self._generate_id("action")
        action = ActionItem(
            id=action_id,
            task=task,
            assigned_to=assigned_to,
            meeting_id=meeting_id,
            decision_id=decision_id,
            due_date=due_date,
            status=ActionStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Add to graph
        self.graph.add_action_item(action)
        
        # Update meeting's action list
        meeting = self.graph.get_meeting(meeting_id)
        if meeting and action_id not in meeting.action_items:
            meeting.action_items.append(action_id)
        
        # Index in embeddings
        embed_text = f"Action Item: {task}"
        if assigned_to:
            person = self.graph.get_person(assigned_to)
            if person:
                embed_text += f"\nAssigned to: {person.name}"
        self.embeddings.add_document(
            doc_id=action_id,
            content=embed_text,
            metadata={
                "type": "action_item",
                "assigned_to": assigned_to or "",
                "meeting_id": meeting_id,
                "source": "realtime"
            }
        )
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Added action: {task[:50]}...")
        return action

    def add_blocker_realtime(
        self,
        description: str,
        reported_by: str = None,
        impact: str = None,
        meeting_id: str = "live_meeting",
        auto_save: bool = True
    ) -> Blocker:
        """
        Add a blocker in real-time during a meeting.
        
        Args:
            description: What is blocked
            reported_by: Person ID who reported it
            impact: Impact description
            meeting_id: Meeting to attach to
            auto_save: Whether to persist immediately
            
        Returns:
            The created Blocker object
        """
        # Ensure meeting exists
        if meeting_id == "live_meeting":
            self.get_or_create_live_meeting()
        
        # Create blocker
        blocker_id = self._generate_id("blocker")
        blocker = Blocker(
            id=blocker_id,
            description=description,
            reported_by=reported_by,
            meeting_id=meeting_id,
            impact=impact,
            resolved=False,
            created_at=datetime.now()
        )
        
        # Add to graph
        self.graph.add_blocker(blocker)
        
        # Update meeting's blocker list
        meeting = self.graph.get_meeting(meeting_id)
        if meeting and blocker_id not in meeting.blockers:
            meeting.blockers.append(blocker_id)
        
        # Index in embeddings
        embed_text = f"Blocker: {description}"
        if impact:
            embed_text += f"\nImpact: {impact}"
        self.embeddings.add_document(
            doc_id=blocker_id,
            content=embed_text,
            metadata={
                "type": "blocker",
                "meeting_id": meeting_id,
                "source": "realtime"
            }
        )
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Added blocker: {description[:50]}...")
        return blocker

    def add_person_realtime(
        self,
        name: str,
        role: str = None,
        email: str = None,
        auto_save: bool = True
    ) -> Person:
        """
        Add a person in real-time.
        
        Args:
            name: Person's name
            role: Their role/title
            email: Email address
            auto_save: Whether to persist immediately
            
        Returns:
            The created Person object
        """
        person_id = name.lower().replace(" ", "_")
        
        # Check if already exists
        existing = self.graph.get_person(person_id)
        if existing:
            return existing
        
        person = Person(
            id=person_id,
            name=name,
            role=role,
            email=email,
            expertise=[]
        )
        
        self.graph.add_person(person)
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Added person: {name}")
        return person

    def resolve_blocker_realtime(
        self,
        blocker_id: str,
        resolution: str,
        auto_save: bool = True
    ) -> Optional[Blocker]:
        """
        Mark a blocker as resolved.
        
        Args:
            blocker_id: ID of the blocker
            resolution: How it was resolved
            auto_save: Whether to persist immediately
            
        Returns:
            The updated Blocker object or None if not found
        """
        blocker = self.graph._blockers.get(blocker_id)
        if not blocker:
            return None
        
        blocker.resolved = True
        blocker.resolution = resolution
        blocker.resolved_at = datetime.now()
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Resolved blocker: {blocker.description[:50]}...")
        return blocker

    def complete_action_realtime(
        self,
        action_id: str,
        auto_save: bool = True
    ) -> Optional[ActionItem]:
        """
        Mark an action item as completed.
        
        Args:
            action_id: ID of the action item
            auto_save: Whether to persist immediately
            
        Returns:
            The updated ActionItem object or None if not found
        """
        action = self.graph._action_items.get(action_id)
        if not action:
            return None
        
        action.status = ActionStatus.COMPLETED
        action.completed_at = datetime.now()
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Completed action: {action.task[:50]}...")
        return action

    def add_note_realtime(
        self,
        content: str,
        category: str = "note",
        meeting_id: str = "live_meeting",
        auto_save: bool = True
    ) -> str:
        """
        Add a free-form note to the knowledge graph.
        
        Args:
            content: The note content
            category: Category tag (e.g., "note", "insight", "question")
            meeting_id: Meeting to attach to
            auto_save: Whether to persist immediately
            
        Returns:
            The note ID
        """
        # Ensure meeting exists
        if meeting_id == "live_meeting":
            self.get_or_create_live_meeting()
        
        note_id = self._generate_id("note")
        
        # Index in embeddings (notes don't go in the graph structure)
        self.embeddings.add_document(
            doc_id=note_id,
            content=content,
            metadata={
                "type": "note",
                "category": category,
                "meeting_id": meeting_id,
                "timestamp": datetime.now().isoformat(),
                "source": "realtime"
            }
        )
        
        if auto_save:
            self._auto_save()
        
        print(f"✓ Added {category}: {content[:50]}...")
        return note_id
