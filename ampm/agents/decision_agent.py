"""
Decision Agent
==============
Tracks decision history, detects conflicts, and manages decision lifecycle.

Responsibilities:
- Track decision history across meetings
- Detect conflicting decisions
- Mark decisions as superseded
- Link related decisions
"""

import os
from typing import Optional
from datetime import datetime

from cerebras.cloud.sdk import Cerebras

from ..models import Decision, DecisionStatus
from ..core.graph import MeetingGraph


class DecisionAgent:
    """
    Agent for managing decisions in the knowledge graph.

    Tracks the full lifecycle of decisions:
    - Created → Confirmed → (Superseded/Reversed)
    """

    def __init__(self, graph: MeetingGraph):
        """
        Initialize the decision agent.

        Args:
            graph: The meeting knowledge graph
        """
        self.graph = graph
        self.cerebras = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    def get_decision_history(self, topic: str) -> list[dict]:
        """
        Get the complete history of decisions on a topic.

        Returns chronological list with context.
        """
        return self.graph.get_decision_history(topic)

    def find_conflicts(self, new_decision: Decision) -> list[dict]:
        """
        Find existing decisions that might conflict with a new one.

        Returns list of potential conflicts with analysis.
        """
        conflicts = []

        # Get decisions on same topic
        if new_decision.topic:
            related = self.graph.get_decisions_by_topic(new_decision.topic)

            for existing in related:
                if existing.id == new_decision.id:
                    continue

                # Skip superseded decisions
                if existing.status == DecisionStatus.SUPERSEDED:
                    continue

                # Check for conflict using LLM
                conflict = self._check_conflict(new_decision, existing)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _check_conflict(self, new: Decision, existing: Decision) -> Optional[dict]:
        """Use LLM to check if two decisions conflict."""
        try:
            response = self.cerebras.chat.completions.create(
                model="llama-3.3-70b",
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze if two decisions conflict. Be concise."
                    },
                    {
                        "role": "user",
                        "content": f"""Do these decisions conflict?

New decision: "{new.content}"
Existing decision: "{existing.content}"

If they conflict, explain briefly. If not, say NO_CONFLICT."""
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()

            if "NO_CONFLICT" in result.upper():
                return None

            return {
                "existing_decision": existing,
                "conflict_analysis": result,
                "severity": "high" if "contradict" in result.lower() else "medium"
            }

        except Exception as e:
            print(f"Error checking conflict: {e}")
            return None

    def supersede(self, old_decision_id: str, new_decision: Decision) -> bool:
        """
        Mark an old decision as superseded by a new one.

        Args:
            old_decision_id: ID of decision being superseded
            new_decision: The new decision that supersedes it

        Returns:
            True if successful
        """
        old_decision = self.graph.get_decision(old_decision_id)
        if not old_decision:
            return False

        # Update old decision
        old_decision.status = DecisionStatus.SUPERSEDED
        old_decision.superseded_by = new_decision.id

        # Add relationship to graph
        self.graph.graph.add_edge(
            new_decision.id,
            old_decision_id,
            relation="supersedes"
        )

        return True

    def get_active_decisions(self, topic: Optional[str] = None) -> list[Decision]:
        """
        Get all active (non-superseded) decisions.

        Args:
            topic: Optional topic filter
        """
        decisions = []

        if topic:
            all_decisions = self.graph.get_decisions_by_topic(topic)
        else:
            all_decisions = list(self.graph._decisions.values())

        for decision in all_decisions:
            if decision.status not in [DecisionStatus.SUPERSEDED, DecisionStatus.REVERSED]:
                decisions.append(decision)

        return sorted(decisions, key=lambda d: d.timestamp, reverse=True)

    def get_decisions_by_person(self, person_name: str) -> list[Decision]:
        """Get all decisions made by a person."""
        person_id = person_name.lower().replace(" ", "_")
        return self.graph.get_decisions_by_person(person_id)

    def summarize_decisions(self, topic: str) -> str:
        """
        Generate a summary of decisions on a topic.

        Useful for onboarding or status updates.
        """
        history = self.get_decision_history(topic)

        if not history:
            return f"No decisions found about '{topic}'"

        try:
            # Format history for LLM
            history_text = ""
            for item in history:
                dec = item["decision"]
                meeting = item.get("meeting")
                person = item.get("made_by")

                history_text += f"\n- {dec.content}"
                if person:
                    history_text += f" (by {person.name})"
                if meeting:
                    history_text += f" [{meeting.title}, {meeting.date.strftime('%Y-%m-%d')}]"
                if dec.status != DecisionStatus.CONFIRMED:
                    history_text += f" [{dec.status.value}]"

            response = self.cerebras.chat.completions.create(
                model="llama-3.3-70b",
                messages=[
                    {
                        "role": "system",
                        "content": "You summarize decision history concisely."
                    },
                    {
                        "role": "user",
                        "content": f"""Summarize the decision history for "{topic}":
{history_text}

Provide a 2-3 sentence summary of the key decisions and current state."""
                    }
                ],
                max_tokens=150,
                temperature=0.5
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Error summarizing: {e}"
