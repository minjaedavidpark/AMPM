"""
Action Item Agent
=================
Tracks action items across meetings, monitors progress, identifies blockers.

Responsibilities:
- Track action item status across meetings
- Identify overdue items
- Link blockers to action items
- Suggest follow-ups
"""

import os
from typing import Optional
from datetime import datetime, timedelta

from cerebras.cloud.sdk import Cerebras

from ..models import ActionItem, ActionStatus, Blocker
from ..core.graph import MeetingGraph


class ActionAgent:
    """
    Agent for managing action items in the knowledge graph.

    Tracks action items from creation to completion,
    monitoring for blockers and overdue items.
    """

    def __init__(self, graph: MeetingGraph):
        """
        Initialize the action agent.

        Args:
            graph: The meeting knowledge graph
        """
        self.graph = graph
        self.cerebras = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    def get_action_items_by_status(self, status: ActionStatus) -> list[ActionItem]:
        """Get all action items with a specific status."""
        return [
            action for action in self.graph._action_items.values()
            if action.status == status
        ]

    def get_pending_actions(self) -> list[ActionItem]:
        """Get all pending (not completed) action items."""
        return [
            action for action in self.graph._action_items.values()
            if action.status in [ActionStatus.PENDING, ActionStatus.IN_PROGRESS]
        ]

    def get_blocked_actions(self) -> list[ActionItem]:
        """Get all blocked action items."""
        return self.get_action_items_by_status(ActionStatus.BLOCKED)

    def get_overdue_actions(self) -> list[ActionItem]:
        """Get all overdue action items."""
        now = datetime.now()
        overdue = []

        for action in self.graph._action_items.values():
            if action.due_date and action.due_date < now:
                if action.status not in [ActionStatus.COMPLETED, ActionStatus.CANCELLED]:
                    overdue.append(action)

        return sorted(overdue, key=lambda a: a.due_date)

    def get_actions_for_person(self, person_name: str) -> list[ActionItem]:
        """Get all action items assigned to a person."""
        person_id = person_name.lower().replace(" ", "_")
        return self.graph.get_action_items_by_person(person_id)

    def get_actions_due_soon(self, days: int = 7) -> list[ActionItem]:
        """Get action items due within the specified number of days."""
        now = datetime.now()
        deadline = now + timedelta(days=days)
        due_soon = []

        for action in self.graph._action_items.values():
            if action.due_date and now <= action.due_date <= deadline:
                if action.status not in [ActionStatus.COMPLETED, ActionStatus.CANCELLED]:
                    due_soon.append(action)

        return sorted(due_soon, key=lambda a: a.due_date)

    def mark_completed(self, action_id: str) -> bool:
        """Mark an action item as completed."""
        action = self.graph._action_items.get(action_id)
        if not action:
            return False

        action.status = ActionStatus.COMPLETED
        action.completed_at = datetime.now()

        # Calculate actual days if we have created_at
        if action.created_at:
            delta = action.completed_at - action.created_at
            action.actual_days = delta.days

        return True

    def mark_blocked(self, action_id: str, blocker_description: str) -> bool:
        """Mark an action item as blocked."""
        action = self.graph._action_items.get(action_id)
        if not action:
            return False

        action.status = ActionStatus.BLOCKED
        action.blocker = blocker_description
        return True

    def unblock(self, action_id: str) -> bool:
        """Unblock an action item."""
        action = self.graph._action_items.get(action_id)
        if not action:
            return False

        action.status = ActionStatus.IN_PROGRESS
        action.blocker = None
        return True

    def get_status_summary(self) -> dict:
        """Get a summary of action item statuses."""
        summary = {
            "total": len(self.graph._action_items),
            "pending": 0,
            "in_progress": 0,
            "blocked": 0,
            "completed": 0,
            "cancelled": 0,
            "overdue": 0
        }

        now = datetime.now()

        for action in self.graph._action_items.values():
            status_key = action.status.value
            if status_key in summary:
                summary[status_key] += 1

            # Check overdue
            if action.due_date and action.due_date < now:
                if action.status not in [ActionStatus.COMPLETED, ActionStatus.CANCELLED]:
                    summary["overdue"] += 1

        # Calculate completion rate
        completable = summary["total"] - summary["cancelled"]
        if completable > 0:
            summary["completion_rate"] = round(summary["completed"] / completable * 100, 1)
        else:
            summary["completion_rate"] = 0

        return summary

    def get_person_workload(self) -> dict:
        """Get workload summary by person."""
        workload = {}

        for action in self.graph._action_items.values():
            if not action.assigned_to:
                continue

            if action.assigned_to not in workload:
                workload[action.assigned_to] = {
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "completed": 0,
                    "overdue": 0
                }

            workload[action.assigned_to]["total"] += 1
            workload[action.assigned_to][action.status.value] += 1

            # Check overdue
            now = datetime.now()
            if action.due_date and action.due_date < now:
                if action.status not in [ActionStatus.COMPLETED, ActionStatus.CANCELLED]:
                    workload[action.assigned_to]["overdue"] += 1

        return workload

    def suggest_follow_ups(self, action_id: str) -> list[str]:
        """
        Suggest follow-up actions based on an action item.

        Uses LLM to generate relevant suggestions.
        """
        action = self.graph._action_items.get(action_id)
        if not action:
            return []

        try:
            # Get context
            context = f"Task: {action.task}\nStatus: {action.status.value}"

            if action.blocker:
                context += f"\nBlocker: {action.blocker}"

            # Get decision context if linked
            if action.decision_id:
                decision = self.graph.get_decision(action.decision_id)
                if decision:
                    context += f"\nRelated decision: {decision.content}"

            response = self.cerebras.chat.completions.create(
                model="llama-3.3-70b",
                messages=[
                    {
                        "role": "system",
                        "content": "You suggest actionable follow-ups for tasks. Be specific and practical."
                    },
                    {
                        "role": "user",
                        "content": f"""Suggest 2-3 follow-up actions for this task:

{context}

Provide specific, actionable suggestions."""
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )

            result = response.choices[0].message.content.strip()

            # Parse suggestions (assume numbered or bulleted list)
            suggestions = []
            for line in result.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line[0] in "-•*"):
                    # Remove leading number/bullet
                    suggestion = line.lstrip("0123456789.-•* ")
                    if suggestion:
                        suggestions.append(suggestion)

            return suggestions[:3]  # Max 3 suggestions

        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []

    def generate_standup_report(self, person_name: str) -> str:
        """
        Generate a standup report for a person.

        Includes: completed items, in-progress items, blockers.
        """
        actions = self.get_actions_for_person(person_name)

        if not actions:
            return f"No action items assigned to {person_name}"

        completed = [a for a in actions if a.status == ActionStatus.COMPLETED]
        in_progress = [a for a in actions if a.status == ActionStatus.IN_PROGRESS]
        blocked = [a for a in actions if a.status == ActionStatus.BLOCKED]
        pending = [a for a in actions if a.status == ActionStatus.PENDING]

        report_parts = [f"Standup Report for {person_name}"]
        report_parts.append("=" * 40)

        if completed:
            report_parts.append("\nCompleted:")
            for a in completed[-3:]:  # Last 3
                report_parts.append(f"  - {a.task}")

        if in_progress:
            report_parts.append("\nIn Progress:")
            for a in in_progress:
                report_parts.append(f"  - {a.task}")

        if blocked:
            report_parts.append("\nBlocked:")
            for a in blocked:
                report_parts.append(f"  - {a.task}")
                if a.blocker:
                    report_parts.append(f"    Blocker: {a.blocker}")

        if pending:
            report_parts.append(f"\nPending: {len(pending)} items")

        return "\n".join(report_parts)
