"""
Meeting Agent
=============
Extracts structured information from meeting data/transcripts.

Responsibilities:
- Parse meeting JSON data
- Extract decisions, action items, blockers
- Identify attendees and their contributions
- Link to related topics and previous meetings
"""

import os
import json
from typing import Optional
from datetime import datetime

from ..models import (
    Meeting, Decision, ActionItem, Blocker, Update, Learning,
    Person, MeetingType, DecisionStatus, ActionStatus
)
from ..core.graph import MeetingGraph
from ..core.embeddings import EmbeddingStore


class MeetingAgent:
    """
    Agent for processing meeting data.

    Extracts structured information and adds to knowledge graph.
    """

    def __init__(self, graph: MeetingGraph, embeddings: Optional[EmbeddingStore] = None):
        """
        Initialize the meeting agent.

        Args:
            graph: The meeting knowledge graph
            embeddings: Optional embedding store for indexing
        """
        self.graph = graph
        self.embeddings = embeddings
        
        # Try Cerebras first, fall back to OpenAI
        self.cerebras = None
        self.openai = None
        
        if os.getenv("CEREBRAS_API_KEY"):
            try:
                from cerebras.cloud.sdk import Cerebras
                self.cerebras = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
            except ImportError:
                pass
        
        if not self.cerebras and os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                pass

    def process_meeting_data(self, data: dict) -> Meeting:
        """
        Process a meeting from JSON data format.

        Expected format:
        {
            "id": "meeting_001",
            "title": "Sprint Planning",
            "date": "2026-05-01",
            "attendees": ["Sarah", "Mike", "Bob"],
            "decisions": [...],
            "action_items": [...],
            "blockers": [...],
            "updates": [...],
            "learnings": [...]
        }
        
        Also supports alternate format with transcript only (auto-extracts):
        {
            "meeting_id": "meeting_001",
            "title": "Sprint Planning",
            "date": "2026-05-01",
            "participants": ["Sarah", "Mike", "Bob"],
            "transcript": "..."
        }
        """
        # Handle alternate field names
        meeting_id = data.get("id") or data.get("meeting_id") or f"meeting_{datetime.now().timestamp()}"
        attendees = data.get("attendees") or data.get("participants") or []

        # Parse date
        date_str = data.get("date", "")
        try:
            date = datetime.fromisoformat(date_str) if date_str else datetime.now()
        except ValueError:
            date = datetime.now()

        # Check if we have transcript but no structured data
        transcript = data.get("transcript")
        has_structured_data = any([
            data.get("decisions"),
            data.get("action_items"),
            data.get("blockers")
        ])
        
        # Auto-extract from transcript if needed (can be slow - uses LLM)
        if transcript and not has_structured_data and not getattr(self, 'skip_extraction', False):
            print(f"  Extracting entities from transcript for {data.get('title', 'meeting')}...")
            try:
                extracted = self.extract_from_transcript(transcript, data.get("title", "Meeting"))
                # Merge extracted data
                data = {**data, **extracted}
            except Exception as e:
                print(f"  Warning: Could not extract from transcript: {e}")

        # Create meeting
        meeting = Meeting(
            id=meeting_id,
            title=data.get("title", "Untitled Meeting"),
            date=date,
            meeting_type=self._parse_meeting_type(data.get("title", "")),
            duration_minutes=data.get("duration_minutes"),
            transcript=transcript,
            summary=data.get("summary"),
            project=data.get("project")
        )

        # Process attendees (handle "Name (Role)" format)
        for attendee_name in attendees:
            # Strip role if present: "Sarah Chen (VP Product)" -> "Sarah Chen"
            if "(" in attendee_name:
                attendee_name = attendee_name.split("(")[0].strip()
            person = self._get_or_create_person(attendee_name)
            meeting.attendees.append(person.id)

        # Process decisions
        for dec_data in data.get("decisions", []):
            decision = self._process_decision(dec_data, meeting_id)
            meeting.decisions.append(decision.id)

        # Process action items
        for action_data in data.get("action_items", []):
            action = self._process_action_item(action_data, meeting_id)
            meeting.action_items.append(action.id)

        # Process blockers
        for blocker_data in data.get("blockers", []):
            blocker = self._process_blocker(blocker_data, meeting_id)
            meeting.blockers.append(blocker.id)

        # Process updates
        for update_data in data.get("updates", []):
            update = self._process_update(update_data, meeting_id)
            meeting.updates.append(update.id)

        # Process learnings
        for learning_data in data.get("learnings", []):
            learning = self._process_learning(learning_data, meeting_id)
            meeting.learnings.append(learning.id)

        # Add meeting to graph
        self.graph.add_meeting(meeting)

        # Index for search
        if self.embeddings:
            self._index_meeting(meeting)

        return meeting

    def _parse_meeting_type(self, title: str) -> MeetingType:
        """Parse meeting type from title."""
        title_lower = title.lower()

        if "standup" in title_lower or "daily" in title_lower:
            return MeetingType.STANDUP
        elif "sprint" in title_lower and "planning" in title_lower:
            return MeetingType.SPRINT_PLANNING
        elif "retro" in title_lower:
            return MeetingType.RETROSPECTIVE
        elif "design" in title_lower and "review" in title_lower:
            return MeetingType.DESIGN_REVIEW
        elif "stakeholder" in title_lower:
            return MeetingType.STAKEHOLDER_SYNC
        elif "1:1" in title_lower or "one on one" in title_lower:
            return MeetingType.ONE_ON_ONE
        elif "all hands" in title_lower:
            return MeetingType.ALL_HANDS
        else:
            return MeetingType.AD_HOC

    def _get_or_create_person(self, name: str) -> Person:
        """Get existing person or create new one."""
        # Simple ID from name
        person_id = name.lower().replace(" ", "_")

        existing = self.graph.get_person(person_id)
        if existing:
            return existing

        person = Person(id=person_id, name=name)
        self.graph.add_person(person)
        return person

    def _process_decision(self, data: dict, meeting_id: str) -> Decision:
        """Process a decision from meeting data."""
        decision_id = data.get("id", f"decision_{datetime.now().timestamp()}")

        # Get person who made the decision
        made_by = data.get("made_by")
        made_by_id = None
        if made_by:
            person = self._get_or_create_person(made_by)
            made_by_id = person.id

        confirmed_by = data.get("confirmed_by")
        confirmed_by_id = None
        if confirmed_by:
            person = self._get_or_create_person(confirmed_by)
            confirmed_by_id = person.id

        decision = Decision(
            id=decision_id,
            content=data.get("decision", ""),
            rationale=data.get("reasoning"),
            topic=data.get("topic"),
            made_by=made_by_id,
            confirmed_by=confirmed_by_id,
            meeting_id=meeting_id,
            quote=data.get("quote"),
            status=DecisionStatus.CONFIRMED
        )

        self.graph.add_decision(decision)

        # Index for search
        if self.embeddings:
            self.embeddings.index_decision(
                decision_id=decision.id,
                content=decision.content,
                rationale=decision.rationale or "",
                meeting_id=meeting_id,
                topic=decision.topic or ""
            )

        return decision

    def _process_action_item(self, data: dict, meeting_id: str) -> ActionItem:
        """Process an action item from meeting data."""
        action_id = data.get("id", f"action_{datetime.now().timestamp()}")

        # Get assigned person
        assigned_to = data.get("assigned_to")
        assigned_to_id = None
        if assigned_to:
            person = self._get_or_create_person(assigned_to)
            assigned_to_id = person.id

        # Parse due date
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(data["due_date"])
            except ValueError:
                pass

        # Parse status
        status_str = data.get("status", "pending").lower()
        status = ActionStatus.PENDING
        if status_str == "completed":
            status = ActionStatus.COMPLETED
        elif status_str == "in_progress":
            status = ActionStatus.IN_PROGRESS
        elif status_str == "blocked":
            status = ActionStatus.BLOCKED

        action = ActionItem(
            id=action_id,
            task=data.get("task", ""),
            assigned_to=assigned_to_id,
            meeting_id=meeting_id,
            decision_id=data.get("decision_id"),  # Link to parent decision
            due_date=due_date,
            status=status,
            estimated_days=data.get("estimated_days")
        )

        self.graph.add_action_item(action)
        return action

    def _process_blocker(self, data: dict, meeting_id: str) -> Blocker:
        """Process a blocker from meeting data."""
        blocker_id = data.get("id", f"blocker_{datetime.now().timestamp()}")

        reported_by = data.get("reported_by")
        reported_by_id = None
        if reported_by:
            person = self._get_or_create_person(reported_by)
            reported_by_id = person.id

        blocker = Blocker(
            id=blocker_id,
            description=data.get("description", ""),
            reported_by=reported_by_id,
            meeting_id=meeting_id,
            impact=data.get("impact"),
            resolution=data.get("resolution_action")
        )

        self.graph._blockers[blocker_id] = blocker
        return blocker

    def _process_update(self, data: dict, meeting_id: str) -> Update:
        """Process a status update from meeting data."""
        update_id = f"update_{datetime.now().timestamp()}"

        person_name = data.get("person", "Unknown")
        person = self._get_or_create_person(person_name)

        update = Update(
            id=update_id,
            person_id=person.id,
            content=data.get("update", ""),
            meeting_id=meeting_id
        )

        return update

    def _process_learning(self, data: dict, meeting_id: str) -> Learning:
        """Process a learning from meeting data."""
        learning_id = f"learning_{datetime.now().timestamp()}"

        learning = Learning(
            id=learning_id,
            lesson=data.get("lesson", ""),
            context=data.get("context"),
            meeting_id=meeting_id
        )

        return learning

    def _index_meeting(self, meeting: Meeting) -> None:
        """Index meeting content for semantic search."""
        if not self.embeddings:
            return

        # Build content from meeting
        content_parts = [meeting.title]

        if meeting.summary:
            content_parts.append(meeting.summary)

        if meeting.transcript:
            # Truncate long transcripts
            content_parts.append(meeting.transcript[:2000])

        content = "\n\n".join(content_parts)

        self.embeddings.index_meeting(
            meeting_id=meeting.id,
            title=meeting.title,
            content=content,
            date=str(meeting.date)
        )

    def extract_from_transcript(self, transcript: str, meeting_title: str) -> dict:
        """
        Use LLM to extract structured data from a transcript.

        Returns dict in the expected meeting data format.
        """
        system_prompt = """You extract structured information from meeting transcripts.
Extract: decisions, action items, blockers, and key updates.
Be precise about WHO said WHAT and any deadlines mentioned.
Return ONLY valid JSON, no other text."""

        user_prompt = f"""Extract structured information from this meeting transcript:

Meeting: {meeting_title}

Transcript:
{transcript}

Return as JSON with this structure:
{{
  "decisions": [{{"decision": "...", "made_by": "...", "topic": "...", "reasoning": "..."}}],
  "action_items": [{{"task": "...", "assigned_to": "...", "due_date": "..."}}],
  "blockers": [{{"description": "...", "reported_by": "...", "impact": "..."}}],
  "summary": "..."
}}"""

        try:
            content = None
            
            # Try Cerebras first
            if self.cerebras:
                response = self.cerebras.chat.completions.create(
                    model="llama-3.3-70b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
                content = response.choices[0].message.content
            
            # Fall back to OpenAI
            elif self.openai:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
                content = response.choices[0].message.content
            
            else:
                print("  Warning: No LLM API available for extraction")
                return {}

            if not content:
                return {}

            # Clean up response - remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Try to extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

            return {}

        except Exception as e:
            print(f"  Error extracting from transcript: {e}")
            return {}
