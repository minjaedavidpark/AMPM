"""
Vector Embeddings for Meeting Memory
====================================
Semantic search across meeting content using vector embeddings.

Integrates with Backboard API for:
- Document storage and indexing
- Automatic vector embeddings
- RAG-based retrieval
- Persistent memory

Falls back to local FAISS for offline use.
"""

import os
from typing import Optional
from dataclasses import dataclass

# Backboard integration (when available)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Local fallback
try:
    import numpy as np
    from openai import OpenAI
    LOCAL_AVAILABLE = True
except ImportError:
    LOCAL_AVAILABLE = False


@dataclass
class SearchResult:
    """A search result with relevance score."""
    id: str
    content: str
    score: float
    metadata: dict
    source: str  # "meeting", "decision", "action_item"


class EmbeddingStore:
    """
    Vector embedding store for semantic search.

    Primary: Backboard API (managed service)
    Fallback: Local OpenAI embeddings + in-memory search
    """

    def __init__(self, use_backboard: bool = True):
        """
        Initialize the embedding store.

        Args:
            use_backboard: Whether to use Backboard API (default True)
        """
        self.use_backboard = use_backboard
        self.backboard_api_key = os.getenv("BACKBOARD_API_KEY")
        self.backboard_base_url = "https://api.backboard.io"

        # Local fallback
        self._documents: list[dict] = []
        self._embeddings: list[list[float]] = []

        if use_backboard and self.backboard_api_key:
            print("EmbeddingStore: Using Backboard API")
        elif LOCAL_AVAILABLE:
            print("EmbeddingStore: Using local embeddings")
            self._openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            print("EmbeddingStore: No embedding backend available")

    # ==================== Backboard API ====================

    def _backboard_request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """Make a request to Backboard API."""
        if not REQUESTS_AVAILABLE or not self.backboard_api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.backboard_api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.backboard_base_url}{endpoint}"

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Backboard API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Backboard API error: {e}")
            return None

    def add_to_backboard(self, doc_id: str, content: str, metadata: dict) -> bool:
        """Add a document to Backboard for indexing."""
        result = self._backboard_request(
            "POST",
            "/v1/documents",
            json={
                "id": doc_id,
                "content": content,
                "metadata": metadata
            }
        )
        return result is not None

    def search_backboard(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search documents via Backboard RAG."""
        result = self._backboard_request(
            "POST",
            "/v1/search",
            json={
                "query": query,
                "top_k": top_k
            }
        )

        if not result:
            return []

        return [
            SearchResult(
                id=r.get("id", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {}),
                source=r.get("metadata", {}).get("source", "unknown")
            )
            for r in result.get("results", [])
        ]

    # ==================== Local Fallback ====================

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI."""
        if not LOCAL_AVAILABLE:
            return []

        response = self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not LOCAL_AVAILABLE:
            return 0.0

        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

    def add_local(self, doc_id: str, content: str, metadata: dict) -> bool:
        """Add a document to local store."""
        if not LOCAL_AVAILABLE:
            return False

        embedding = self._get_embedding(content)
        self._documents.append({
            "id": doc_id,
            "content": content,
            "metadata": metadata
        })
        self._embeddings.append(embedding)
        return True

    def search_local(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search documents locally."""
        if not LOCAL_AVAILABLE or not self._documents:
            return []

        query_embedding = self._get_embedding(query)

        # Compute similarities
        similarities = []
        for i, doc_embedding in enumerate(self._embeddings):
            score = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, score))

        # Sort by score
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k
        results = []
        for i, score in similarities[:top_k]:
            doc = self._documents[i]
            results.append(SearchResult(
                id=doc["id"],
                content=doc["content"],
                score=score,
                metadata=doc["metadata"],
                source=doc["metadata"].get("source", "unknown")
            ))

        return results

    # ==================== Public Interface ====================

    def add(self, doc_id: str, content: str, metadata: dict) -> bool:
        """
        Add a document for semantic search.

        Args:
            doc_id: Unique document identifier
            content: Text content to index
            metadata: Additional metadata (source, date, etc.)
        """
        if self.use_backboard and self.backboard_api_key:
            return self.add_to_backboard(doc_id, content, metadata)
        else:
            return self.add_local(doc_id, content, metadata)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        Search for relevant documents.

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if self.use_backboard and self.backboard_api_key:
            results = self.search_backboard(query, top_k)
            if results:
                return results
            # Fall back to local if Backboard fails
            print("Backboard search failed, falling back to local")

        return self.search_local(query, top_k)

    def index_meeting(self, meeting_id: str, title: str, content: str, date: str) -> bool:
        """Index a meeting for search."""
        return self.add(
            doc_id=f"meeting:{meeting_id}",
            content=f"{title}\n\n{content}",
            metadata={
                "source": "meeting",
                "meeting_id": meeting_id,
                "title": title,
                "date": date
            }
        )

    def index_decision(self, decision_id: str, content: str, rationale: str,
                       meeting_id: str, topic: str) -> bool:
        """Index a decision for search."""
        return self.add(
            doc_id=f"decision:{decision_id}",
            content=f"Decision: {content}\nRationale: {rationale}",
            metadata={
                "source": "decision",
                "decision_id": decision_id,
                "meeting_id": meeting_id,
                "topic": topic
            }
        )

    @property
    def document_count(self) -> int:
        """Number of indexed documents."""
        return len(self._documents)

    # ==================== Persistence ====================

    def save(self, filepath: str) -> None:
        """
        Save the embedding store to a file.
        
        Args:
            filepath: Path to save (JSON format)
        """
        import json
        from pathlib import Path
        
        data = {
            "version": "1.0",
            "documents": self._documents,
            "embeddings": self._embeddings
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        print(f"Embeddings saved to {filepath} ({len(self._documents)} documents)")

    def load(self, filepath: str) -> bool:
        """
        Load the embedding store from a file.
        
        Args:
            filepath: Path to load from
            
        Returns:
            True if loaded successfully, False otherwise
        """
        import json
        from pathlib import Path
        
        if not Path(filepath).exists():
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self._documents = data.get("documents", [])
            self._embeddings = data.get("embeddings", [])
            
            print(f"Embeddings loaded from {filepath} ({len(self._documents)} documents)")
            return True
            
        except Exception as e:
            print(f"Error loading embeddings: {e}")
            return False
