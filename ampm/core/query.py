"""
Context Query Engine
====================
Natural language queries against meeting memory.

"Why did we decide X?" → Answer with sources in 2 seconds

Combines:
1. Vector search (semantic similarity)
2. Graph traversal (relationships)
3. LLM synthesis (answer generation)
"""

import os
import time
from typing import Optional
from dataclasses import dataclass

from .graph import MeetingGraph
from .embeddings import EmbeddingStore, SearchResult


@dataclass
class QueryResult:
    """Result of a context query."""
    answer: str
    sources: list[dict]
    query_time_ms: float
    confidence: float


class QueryEngine:
    """
    Natural language query engine for meeting memory.

    Answers questions like:
    - "Why did we choose Stripe?"
    - "Who decided to delay internationalization?"
    - "What's blocking the payments launch?"
    - "What happened in last week's sprint planning?"
    """

    def __init__(self, graph: MeetingGraph, embeddings: Optional[EmbeddingStore] = None):
        """
        Initialize the query engine.

        Args:
            graph: The meeting knowledge graph
            embeddings: Optional embedding store for semantic search
        """
        self.graph = graph
        self.embeddings = embeddings or EmbeddingStore()

        # Initialize LLM - try Cerebras first, fall back to OpenAI
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

    def query(self, question: str, top_k: int = 5) -> QueryResult:
        """
        Answer a natural language question about meeting history.

        Args:
            question: Natural language question
            top_k: Number of relevant sources to retrieve

        Returns:
            QueryResult with answer, sources, and timing
        """
        start_time = time.time()

        # Step 1: Semantic search for relevant content
        search_results = self.embeddings.search(question, top_k=top_k)

        # Step 2: Enrich with graph context
        enriched_context = self._enrich_with_graph(search_results)

        # Step 3: Generate answer with Cerebras
        answer, confidence = self._generate_answer(question, enriched_context)

        query_time_ms = (time.time() - start_time) * 1000

        return QueryResult(
            answer=answer,
            sources=enriched_context,
            query_time_ms=query_time_ms,
            confidence=confidence
        )

    def _enrich_with_graph(self, search_results: list[SearchResult]) -> list[dict]:
        """
        Enrich search results with graph context.

        For each result, add:
        - Related decisions
        - People involved
        - Meeting context
        """
        enriched = []

        for result in search_results:
            context = {
                "id": result.id,
                "content": result.content,
                "score": result.score,
                "source_type": result.source,
                "metadata": result.metadata
            }

            # Add graph context based on source type
            if result.source == "meeting":
                meeting_id = result.metadata.get("meeting_id")
                if meeting_id:
                    meeting = self.graph.get_meeting(meeting_id)
                    if meeting:
                        context["meeting_title"] = meeting.title
                        context["meeting_date"] = str(meeting.date)
                        context["attendees"] = meeting.attendees
                        # Get decisions from this meeting
                        decisions = self.graph.get_decisions_by_meeting(meeting_id)
                        context["decisions"] = [
                            {"content": d.content, "made_by": d.made_by}
                            for d in decisions
                        ]

            elif result.source == "decision":
                decision_id = result.metadata.get("decision_id")
                if decision_id:
                    decision = self.graph.get_decision(decision_id)
                    if decision:
                        context["decision_content"] = decision.content
                        context["rationale"] = decision.rationale
                        context["made_by"] = decision.made_by
                        context["quote"] = decision.quote
                        # Get upstream context (meeting)
                        if decision.meeting_id:
                            meeting = self.graph.get_meeting(decision.meeting_id)
                            if meeting:
                                context["meeting_title"] = meeting.title
                                context["meeting_date"] = str(meeting.date)

            enriched.append(context)

        return enriched

    def _generate_answer(self, question: str, context: list[dict]) -> tuple[str, float]:
        """
        Generate an answer using Cerebras LLM.

        Returns (answer, confidence_score)
        """
        # Format context for prompt
        context_text = self._format_context(context)

        system_prompt = """You are AMPM, an AI meeting assistant that helps teams remember decisions and track action items.

Your role:
- Answer questions about past meetings, decisions, and action items
- Be concise and direct (2-3 sentences for spoken responses, more detail for written)
- Always cite the specific meeting date and who made the decision
- Include direct quotes when available
- If you don't have enough information, say so clearly

Important: Cite your sources. Reference specific meetings and people."""

        user_prompt = f"""Based on the following meeting context, answer this question:

Question: {question}

Context:
{context_text}

Provide a clear, sourced answer. If the information isn't in the context, say so."""

        try:
            answer = None
            
            # Try Cerebras first
            if self.cerebras:
                response = self.cerebras.chat.completions.create(
                    model="llama-3.3-70b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
            
            # Fall back to OpenAI
            elif self.openai:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
            
            else:
                return "No LLM API available. Please set OPENAI_API_KEY or CEREBRAS_API_KEY.", 0.0

            # Simple confidence based on context availability
            confidence = min(1.0, len(context) / 3)

            return answer, confidence

        except Exception as e:
            return f"Error generating answer: {e}", 0.0

    def _format_context(self, context: list[dict]) -> str:
        """Format context for the LLM prompt."""
        parts = []

        for i, ctx in enumerate(context, 1):
            part = f"--- Source {i} ---\n"

            if ctx.get("meeting_title"):
                part += f"Meeting: {ctx['meeting_title']}"
                if ctx.get("meeting_date"):
                    part += f" ({ctx['meeting_date']})"
                part += "\n"

            if ctx.get("decision_content"):
                part += f"Decision: {ctx['decision_content']}\n"
                if ctx.get("rationale"):
                    part += f"Rationale: {ctx['rationale']}\n"
                if ctx.get("made_by"):
                    part += f"Made by: {ctx['made_by']}\n"
                if ctx.get("quote"):
                    part += f"Quote: \"{ctx['quote']}\"\n"

            if ctx.get("content") and not ctx.get("decision_content"):
                part += f"Content: {ctx['content']}\n"

            parts.append(part)

        return "\n".join(parts)

    # ==================== Convenience Methods ====================

    def why(self, topic: str) -> QueryResult:
        """Shortcut for 'Why did we decide X?' queries."""
        return self.query(f"Why did we decide {topic}?")

    def who(self, topic: str) -> QueryResult:
        """Shortcut for 'Who decided X?' queries."""
        return self.query(f"Who decided {topic}?")

    def what_happened(self, topic: str) -> QueryResult:
        """Shortcut for 'What happened with X?' queries."""
        return self.query(f"What happened with {topic}?")

    def status(self, topic: str) -> QueryResult:
        """Shortcut for 'What's the status of X?' queries."""
        return self.query(f"What's the current status of {topic}?")
