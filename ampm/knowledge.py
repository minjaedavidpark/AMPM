"""
Meeting Knowledge Base
======================
Loads and provides access to meeting history data.
"""

import json
from pathlib import Path
from typing import Optional


class MeetingKnowledge:
    """Loads and provides access to meeting data."""

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the meeting knowledge base.

        Args:
            data_path: Path to meeting data JSON file.
                      Defaults to data/sample_meetings.json in project root.
        """
        if data_path is None:
            # Default to project root data folder
            self.data_path = Path(__file__).parent.parent / "data" / "sample_meetings.json"
        else:
            self.data_path = Path(data_path)

        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Load meeting data from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Meeting data not found: {self.data_path}")

        with open(self.data_path, 'r') as f:
            return json.load(f)

    def get_context(self) -> str:
        """Format meeting data as context for the LLM."""
        meetings = self.data.get("meetings", [])

        context_parts = [
            f"Project: {self.data.get('project', 'Unknown')}",
            f"Team: {json.dumps(self.data.get('team', {}))}",
            "",
            "=== MEETING HISTORY ==="
        ]

        for meeting in meetings:
            context_parts.append(f"\n--- {meeting['title']} ({meeting['date']}) ---")
            context_parts.append(f"Attendees: {', '.join(meeting['attendees'])}")

            # Decisions
            for decision in meeting.get("decisions", []):
                context_parts.append(f"\nDECISION: {decision['decision']}")
                context_parts.append(f"  Topic: {decision['topic']}")
                context_parts.append(f"  Reasoning: {decision.get('reasoning', 'Not specified')}")
                context_parts.append(f"  Made by: {decision.get('made_by', 'Unknown')}")
                if decision.get('confirmed_by'):
                    context_parts.append(f"  Confirmed by: {decision['confirmed_by']}")
                if decision.get('quote'):
                    context_parts.append(f"  Quote: \"{decision['quote']}\"")

            # Action items
            for action in meeting.get("action_items", []):
                context_parts.append(f"\nACTION ITEM: {action['task']}")
                context_parts.append(f"  Assigned to: {action['assigned_to']}")
                context_parts.append(f"  Due: {action['due_date']}")
                context_parts.append(f"  Status: {action['status']}")

            # Blockers
            for blocker in meeting.get("blockers", []):
                context_parts.append(f"\nBLOCKER: {blocker['description']}")
                context_parts.append(f"  Reported by: {blocker['reported_by']}")
                context_parts.append(f"  Impact: {blocker['impact']}")
                context_parts.append(f"  Resolution: {blocker.get('resolution_action', 'Pending')}")

            # Updates
            for update in meeting.get("updates", []):
                context_parts.append(f"\nUPDATE from {update['person']}: {update['update']}")

            # Learnings
            for learning in meeting.get("learnings", []):
                context_parts.append(f"\nLEARNING: {learning['lesson']}")
                context_parts.append(f"  Context: {learning['context']}")

        return "\n".join(context_parts)

    @property
    def meeting_count(self) -> int:
        """Return number of meetings in the knowledge base."""
        return len(self.data.get("meetings", []))

    @property
    def project_name(self) -> str:
        """Return the project name."""
        return self.data.get("project", "Unknown")
