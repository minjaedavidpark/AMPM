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
                print("QueryEngine: Using Cerebras")
            except ImportError:
                pass
        
        if not self.cerebras and os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                import httpx
                # Set longer timeout for OpenAI client
                self.openai = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    timeout=httpx.Timeout(60.0, connect=10.0)
                )
                print("QueryEngine: Using OpenAI")
            except ImportError:
                pass
        
        if not self.cerebras and not self.openai:
            print("QueryEngine: WARNING - No LLM API available")

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
        print(f"Searching for: {question}")
        search_results = self.embeddings.search(question, top_k=top_k)
        print(f"Found {len(search_results)} search results")

        # Step 2: Enrich with graph context
        enriched_context = self._enrich_with_graph(search_results)
        print(f"Enriched to {len(enriched_context)} context items")

        # If no search results, try to get context from graph directly
        if not enriched_context:
            print("No search results, trying graph query...")
            # Get some decisions as fallback context
            all_decisions = list(self.graph._decisions.values())[:5]
            for dec in all_decisions:
                enriched_context.append({
                    "id": dec.id,
                    "content": dec.content,
                    "decision_content": dec.content,
                    "rationale": dec.rationale,
                    "made_by": dec.made_by,
                    "source_type": "decision",
                    "meeting_id": dec.meeting_id
                })
            print(f"Added {len(enriched_context)} decisions from graph as fallback")

        # Step 3: Generate answer with LLM
        print("Generating answer...")
        # Debug: Show what we're sending to the LLM
        if enriched_context:
            print(f"DEBUG: First context item keys: {list(enriched_context[0].keys())}")
            ctx0 = enriched_context[0]
            print(f"DEBUG: decision_content = {ctx0.get('decision_content')}")
            print(f"DEBUG: meeting_title = {ctx0.get('meeting_title')}")
        answer, confidence = self._generate_answer(question, enriched_context)
        print(f"Answer generated with confidence {confidence}")

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

        # Retry logic for resilience
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
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
                        temperature=0.7,
                        timeout=30.0  # 30 second timeout
                    )
                    answer = response.choices[0].message.content
                
                else:
                    return "No LLM API available. Please set OPENAI_API_KEY or CEREBRAS_API_KEY.", 0.0

                if answer:
                    # Simple confidence based on context availability
                    confidence = min(1.0, len(context) / 3)
                    return answer, confidence
                    
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                    time.sleep(1)  # Brief pause before retry
                continue
        
        # If we have context but LLM failed, provide a basic answer from context
        if context:
            # Build a simple answer from context without LLM
            fallback_parts = ["Based on the meeting records I found:"]
            
            for ctx in context[:5]:
                if ctx.get("decision_content"):
                    part = f"\n**Decision:** {ctx['decision_content']}"
                    if ctx.get("rationale"):
                        part += f"\n  - Rationale: {ctx['rationale']}"
                    if ctx.get("made_by"):
                        part += f"\n  - Made by: {ctx['made_by']}"
                    if ctx.get("meeting_title"):
                        part += f"\n  - From: {ctx['meeting_title']} ({ctx.get('meeting_date', 'unknown date')})"
                    fallback_parts.append(part)
                elif ctx.get("content"):
                    content = ctx['content'][:300]
                    if ctx.get("meeting_title"):
                        fallback_parts.append(f"\n**From {ctx['meeting_title']}:** {content}...")
                    else:
                        fallback_parts.append(f"\n{content}...")
            
            if len(fallback_parts) > 1:
                if last_error:
                    fallback_parts.append(f"\n\n*(Note: LLM synthesis unavailable - showing raw results. Error: {str(last_error)[:100]})*")
                return "\n".join(fallback_parts), 0.5
        
        error_msg = str(last_error) if last_error else "Unknown error"
        return f"Could not generate answer. Error: {error_msg}", 0.0

    def _format_context(self, context: list[dict]) -> str:
        """Format context for the LLM prompt."""
        if not context:
            return "No context available."

        parts = []

        for i, ctx in enumerate(context, 1):
            lines = [f"--- Source {i} ---"]

            # Debug: print what we're working with
            print(f"  Formatting source {i}: keys={list(ctx.keys())[:5]}...")

            # Add meeting info if available
            meeting_title = ctx.get("meeting_title")
            meeting_date = ctx.get("meeting_date")
            if meeting_title:
                meeting_line = f"Meeting: {meeting_title}"
                if meeting_date:
                    meeting_line += f" ({meeting_date})"
                lines.append(meeting_line)

            # Add decision info if available
            decision_content = ctx.get("decision_content")
            if decision_content:
                lines.append(f"Decision: {decision_content}")
                rationale = ctx.get("rationale")
                if rationale:
                    lines.append(f"Rationale: {rationale}")
                made_by = ctx.get("made_by")
                if made_by:
                    lines.append(f"Made by: {made_by}")
                quote = ctx.get("quote")
                if quote:
                    lines.append(f"Quote: \"{quote}\"")

            # Add content for non-decision items or as fallback
            content = ctx.get("content")
            if content and not decision_content:
                lines.append(f"Content: {content[:500]}")

            # Fallback: if we only have the header, add whatever content we can find
            if len(lines) == 1:
                if content:
                    lines.append(f"Content: {content[:500]}")
                elif ctx.get("metadata"):
                    # Try to extract info from metadata
                    meta = ctx.get("metadata", {})
                    if meta.get("topic"):
                        lines.append(f"Topic: {meta.get('topic')}")

            part = "\n".join(lines)
            parts.append(part)

        formatted = "\n\n".join(parts)
        print(f"  Formatted {len(parts)} sources, total length: {len(formatted)}")
        return formatted

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

    def query_fast(self, question: str) -> QueryResult:
        """
        Fast query using Backboard's integrated memory + LLM.

        Skips local graph enrichment and uses Backboard's memory-augmented
        RAG directly. Best for simple factual questions.

        Falls back to full query() if Backboard isn't available or errors.
        """
        start_time = time.time()

        # Try Backboard's integrated RAG if available
        if (self.embeddings.use_backboard and
            self.embeddings.backboard_api_key and
            self.embeddings.thread_id):

            try:
                answer, memories = self.embeddings.query_with_context(question)

                if answer:
                    # Check if answer is an error message
                    if "Error" in answer and ("402" in answer or "credits" in answer.lower()):
                        print("Backboard API out of credits, falling back to local query...")
                        return self.query(question)

                    query_time_ms = (time.time() - start_time) * 1000
                    sources = [
                        {
                            "id": m.id,
                            "content": m.content,
                            "score": m.score,
                            "source_type": "backboard_memory"
                        }
                        for m in memories
                    ]
                    confidence = min(1.0, len(memories) / 3) if memories else 0.5

                    return QueryResult(
                        answer=answer,
                        sources=sources,
                        query_time_ms=query_time_ms,
                        confidence=confidence
                    )
            except Exception as e:
                print(f"Backboard query failed: {e}, falling back to local query...")

        # Fallback to full query
        return self.query(question)
