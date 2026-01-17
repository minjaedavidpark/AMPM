"""
Ripple Detection Engine
=======================
Detect downstream impacts when decisions change.

When a decision is modified:
1. Find all connected nodes (action items, other decisions)
2. Analyze each for conflicts
3. Generate impact report

"If we change X, what else is affected?"
"""

import os
import time
from typing import Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from cerebras.cloud.sdk import Cerebras

from .graph import MeetingGraph
from ..models import Decision, ActionItem, ActionStatus


@dataclass
class Impact:
    """An impacted artifact."""
    id: str
    type: str  # "decision", "action_item", "meeting"
    title: str
    severity: str  # "critical", "high", "medium", "low"
    reason: str
    suggestion: str


@dataclass
class RippleReport:
    """Report of all downstream impacts from a change."""
    change_description: str
    total_affected: int
    impacts: list[Impact]
    people_to_notify: list[str]
    suggestions: list[str]
    analysis_time_ms: float


class RippleDetector:
    """
    Detects downstream impacts when decisions change.

    Use cases:
    - "If we switch from OAuth to SAML, what breaks?"
    - "If we delay this feature, what action items are affected?"
    - "If we change this requirement, who needs to know?"
    """

    def __init__(self, graph: MeetingGraph):
        """
        Initialize the ripple detector.

        Args:
            graph: The meeting knowledge graph
        """
        self.graph = graph
        self.cerebras = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    def detect(self, decision_id: str, new_value: str,
               old_value: Optional[str] = None) -> RippleReport:
        """
        Detect ripple effects from changing a decision.

        Args:
            decision_id: ID of the decision being changed
            new_value: New decision content
            old_value: Previous decision content (optional, will look up)

        Returns:
            RippleReport with all impacts
        """
        start_time = time.time()

        # Get the original decision
        decision = self.graph.get_decision(decision_id)
        if not decision:
            return RippleReport(
                change_description=f"Decision {decision_id} not found",
                total_affected=0,
                impacts=[],
                people_to_notify=[],
                suggestions=[],
                analysis_time_ms=0
            )

        if old_value is None:
            old_value = decision.content

        change_description = f"Change: '{old_value}' → '{new_value}'"

        # Get all dependent nodes (action items that follow from this decision)
        dependent_ids = self._get_dependent_nodes(decision_id)

        # Analyze each dependent node for impact
        impacts = self._analyze_impacts(
            dependent_ids,
            old_value,
            new_value
        )

        # Collect people to notify
        people_to_notify = self._get_people_to_notify(impacts)

        # Generate suggestions
        suggestions = self._generate_suggestions(impacts, new_value)

        analysis_time_ms = (time.time() - start_time) * 1000

        return RippleReport(
            change_description=change_description,
            total_affected=len(impacts),
            impacts=impacts,
            people_to_notify=people_to_notify,
            suggestions=suggestions,
            analysis_time_ms=analysis_time_ms
        )

    def _get_dependent_nodes(self, decision_id: str) -> list[str]:
        """
        Get all nodes that depend on a decision.

        This includes:
        - Action items that follow from this decision
        - Other decisions with the same topic
        """
        dependent_ids = []

        # Find action items that depend on this decision
        for action_id, action in self.graph._action_items.items():
            if action.decision_id == decision_id:
                dependent_ids.append(action_id)

        # Find related decisions (same topic)
        decision = self.graph.get_decision(decision_id)
        if decision and decision.topic:
            for other_id, other_dec in self.graph._decisions.items():
                if other_id != decision_id and other_dec.topic == decision.topic:
                    dependent_ids.append(other_id)

        return dependent_ids

    def _analyze_impacts(self, node_ids: list[str],
                         old_value: str, new_value: str) -> list[Impact]:
        """
        Analyze each downstream node for impact.
        Uses parallel LLM calls for speed.
        """
        impacts = []

        # Group nodes by type
        decisions = []
        action_items = []

        for node_id in node_ids:
            if node_id in self.graph._decisions:
                decisions.append(self.graph._decisions[node_id])
            elif node_id in self.graph._action_items:
                action_items.append(self.graph._action_items[node_id])

        # Analyze action items (parallel)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            for action in action_items:
                future = executor.submit(
                    self._analyze_action_item_impact,
                    action, old_value, new_value
                )
                futures.append(future)

            for future in as_completed(futures):
                impact = future.result()
                if impact:
                    impacts.append(impact)

        # Analyze related decisions
        for decision in decisions:
            impact = self._analyze_decision_impact(decision, old_value, new_value)
            if impact:
                impacts.append(impact)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        impacts.sort(key=lambda x: severity_order.get(x.severity, 4))

        return impacts

    def _analyze_action_item_impact(self, action: ActionItem,
                                    old_value: str, new_value: str) -> Optional[Impact]:
        """Analyze if an action item is impacted by the change."""
        # Skip completed actions
        if action.status == ActionStatus.COMPLETED:
            return None

        # Quick heuristic check
        old_keywords = set(old_value.lower().split())
        action_keywords = set(action.task.lower().split())

        # If no keyword overlap, likely not impacted
        if not old_keywords & action_keywords:
            return None

        # Use LLM for detailed analysis
        try:
            response = self.cerebras.chat.completions.create(
                model="llama-3.3-70b",
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze if a task is impacted by a decision change. Be concise."
                    },
                    {
                        "role": "user",
                        "content": f"""Is this action item affected by the decision change?

Decision change: "{old_value}" → "{new_value}"

Action item: "{action.task}"
Status: {action.status.value}

If affected, respond with:
SEVERITY: [critical/high/medium/low]
REASON: [brief explanation]
SUGGESTION: [what to do]

If not affected, respond with just: NOT_AFFECTED"""
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()

            if "NOT_AFFECTED" in result:
                return None

            # Parse response
            lines = result.split("\n")
            severity = "medium"
            reason = "May be affected by decision change"
            suggestion = "Review and update if needed"

            for line in lines:
                if line.startswith("SEVERITY:"):
                    severity = line.replace("SEVERITY:", "").strip().lower()
                elif line.startswith("REASON:"):
                    reason = line.replace("REASON:", "").strip()
                elif line.startswith("SUGGESTION:"):
                    suggestion = line.replace("SUGGESTION:", "").strip()

            return Impact(
                id=action.id,
                type="action_item",
                title=action.task,
                severity=severity,
                reason=reason,
                suggestion=suggestion
            )

        except Exception as e:
            print(f"Error analyzing action item: {e}")
            return None

    def _analyze_decision_impact(self, decision: Decision,
                                 old_value: str, new_value: str) -> Optional[Impact]:
        """Analyze if a related decision conflicts with the change."""
        # Check for potential contradiction
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
                        "content": f"""Does this new decision conflict with an existing one?

New decision: "{new_value}"
Existing decision: "{decision.content}"

If they conflict, respond with:
SEVERITY: [critical/high/medium/low]
REASON: [brief explanation]

If no conflict, respond with: NO_CONFLICT"""
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()

            if "NO_CONFLICT" in result:
                return None

            # Parse response
            lines = result.split("\n")
            severity = "high"
            reason = "May conflict with existing decision"

            for line in lines:
                if line.startswith("SEVERITY:"):
                    severity = line.replace("SEVERITY:", "").strip().lower()
                elif line.startswith("REASON:"):
                    reason = line.replace("REASON:", "").strip()

            return Impact(
                id=decision.id,
                type="decision",
                title=decision.content[:50] + "..." if len(decision.content) > 50 else decision.content,
                severity=severity,
                reason=reason,
                suggestion="Review for consistency with new decision"
            )

        except Exception as e:
            print(f"Error analyzing decision: {e}")
            return None

    def _get_people_to_notify(self, impacts: list[Impact]) -> list[str]:
        """Get list of people who should be notified about impacts."""
        people = set()

        for impact in impacts:
            if impact.type == "action_item":
                action = self.graph._action_items.get(impact.id)
                if action and action.assigned_to:
                    people.add(action.assigned_to)
            elif impact.type == "decision":
                decision = self.graph._decisions.get(impact.id)
                if decision and decision.made_by:
                    people.add(decision.made_by)

        return list(people)

    def _generate_suggestions(self, impacts: list[Impact], new_value: str) -> list[str]:
        """Generate actionable suggestions based on impacts."""
        suggestions = []

        critical_count = sum(1 for i in impacts if i.severity == "critical")
        high_count = sum(1 for i in impacts if i.severity == "high")
        action_count = sum(1 for i in impacts if i.type == "action_item")

        if critical_count > 0:
            suggestions.append(f"⚠️ {critical_count} critical impact(s) - address before proceeding")

        if high_count > 0:
            suggestions.append(f"Review {high_count} high-priority item(s)")

        if action_count > 0:
            suggestions.append(f"Update or reassign {action_count} affected action item(s)")

        if not suggestions:
            suggestions.append("Change appears safe - minimal downstream impact")

        return suggestions

    # ==================== Convenience Methods ====================

    def what_if(self, topic: str, change: str) -> RippleReport:
        """
        Convenience method for "what if" scenarios.

        Example: what_if("payment provider", "switch to PayPal")
        """
        # Find decisions about this topic
        decisions = self.graph.get_decisions_by_topic(topic)

        if not decisions:
            return RippleReport(
                change_description=f"No decisions found about '{topic}'",
                total_affected=0,
                impacts=[],
                people_to_notify=[],
                suggestions=["No existing decisions to analyze"],
                analysis_time_ms=0
            )

        # Use the most recent decision
        latest = max(decisions, key=lambda d: d.timestamp)
        return self.detect(latest.id, change, latest.content)
