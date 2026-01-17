"""
Vector Embeddings for Meeting Memory
====================================
Semantic search across meeting content using vector embeddings.

Integrates with Backboard API for:
- Document storage and indexing
- Automatic vector embeddings
- RAG-based retrieval (via threads with memory=Auto)
- Persistent memory across sessions

Falls back to local OpenAI embeddings for offline use.
"""

import os
import json
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

    Primary: Backboard API (managed service with persistent memory)
    Fallback: Local OpenAI embeddings + in-memory search

    Backboard Integration:
    - Uses assistants/threads model for conversation memory
    - Memory is automatically stored and retrieved
    - Supports Cerebras for fast inference
    """

    # Default assistant and model configuration
    DEFAULT_ASSISTANT_NAME = "AMPM-Meeting-Memory"
    DEFAULT_LLM_PROVIDER = "cerebras"
    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
    DEFAULT_CONFIG_DIR = ".ampm"
    CONFIG_FILENAME = "backboard_state.json"

    def __init__(
        self,
        use_backboard: bool = True,
        assistant_id: Optional[str] = None,
        config_dir: Optional[str] = None,
        persist: bool = True
    ):
        """
        Initialize the embedding store.

        Args:
            use_backboard: Whether to use Backboard API (default True)
            assistant_id: Optional Backboard assistant ID. If not provided,
                         will create or find one named AMPM-Meeting-Memory.
            config_dir: Directory to store persistent state (default .ampm)
            persist: Whether to persist thread_id across sessions (default True)
        """
        self.use_backboard = use_backboard
        self.backboard_api_key = os.getenv("BACKBOARD_API_KEY")
        self.backboard_base_url = "https://app.backboard.io/api"
        self.persist = persist

        # Config directory for persistence
        if config_dir:
            self.config_dir = config_dir
        else:
            self.config_dir = os.path.join(os.getcwd(), self.DEFAULT_CONFIG_DIR)

        # Backboard state
        self.assistant_id = assistant_id
        self.thread_id: Optional[str] = None

        # Local fallback
        self._documents: list[dict] = []
        self._embeddings: list[list[float]] = []
        self._openai = None

        # Always initialize local OpenAI client as fallback for embeddings
        if LOCAL_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self._openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("EmbeddingStore: OpenAI embeddings initialized")
        
        if use_backboard and self.backboard_api_key:
            print("EmbeddingStore: Using Backboard API")
            self._init_backboard()
        elif LOCAL_AVAILABLE and self._openai:
            print("EmbeddingStore: Using local embeddings")
        else:
            print("EmbeddingStore: No embedding backend available")

    # ==================== Backboard API ====================

    def _backboard_request(
        self, method: str, endpoint: str,
        json_data: Optional[dict] = None,
        form_data: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Make a request to Backboard API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /assistants)
            json_data: JSON body (for application/json requests)
            form_data: Form data (for multipart/form-data requests)
        """
        if not REQUESTS_AVAILABLE or not self.backboard_api_key:
            return None

        headers = {"X-API-Key": self.backboard_api_key}
        url = f"{self.backboard_base_url}{endpoint}"

        try:
            if form_data:
                # Multipart form data (for messages endpoint)
                response = requests.request(method, url, headers=headers, data=form_data)
            elif json_data is not None:
                # JSON body (even if empty dict)
                headers["Content-Type"] = "application/json"
                response = requests.request(method, url, headers=headers, json=json_data)
            else:
                response = requests.request(method, url, headers=headers)

            if response.status_code in (200, 201):
                return response.json()
            else:
                print(f"Backboard API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Backboard API error: {e}")
            return None

    def _init_backboard(self):
        """Initialize Backboard assistant and thread with persistence."""
        # Try to load persisted state
        if self.persist:
            self._load_state()

        # Get or create assistant
        if not self.assistant_id:
            self.assistant_id = self._get_or_create_assistant()

        # Validate existing thread or create new one
        if self.thread_id:
            if self._validate_thread():
                print(f"EmbeddingStore: Restored thread {self.thread_id[:8]}...")
            else:
                print(f"EmbeddingStore: Thread expired, creating new one")
                self.thread_id = None

        if self.assistant_id and not self.thread_id:
            self.thread_id = self._create_thread()
            if self.thread_id:
                print(f"EmbeddingStore: Thread {self.thread_id[:8]}... ready")
                if self.persist:
                    self._save_state()

    def _validate_thread(self) -> bool:
        """Check if the persisted thread still exists."""
        if not self.thread_id:
            return False

        result = self._backboard_request("GET", f"/threads/{self.thread_id}")
        return result is not None and "thread_id" in result

    def _get_config_path(self) -> str:
        """Get the full path to the config file."""
        return os.path.join(self.config_dir, self.CONFIG_FILENAME)

    def _save_state(self) -> bool:
        """Save assistant_id and thread_id to disk."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            state = {
                "assistant_id": self.assistant_id,
                "thread_id": self.thread_id,
                "assistant_name": self.DEFAULT_ASSISTANT_NAME
            }
            with open(self._get_config_path(), 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
            return False

    def _load_state(self) -> bool:
        """Load assistant_id and thread_id from disk."""
        try:
            config_path = self._get_config_path()
            if not os.path.exists(config_path):
                return False

            with open(config_path, 'r') as f:
                state = json.load(f)

            # Only restore if same assistant name
            if state.get("assistant_name") == self.DEFAULT_ASSISTANT_NAME:
                self.assistant_id = state.get("assistant_id")
                self.thread_id = state.get("thread_id")
                return True
            return False
        except Exception as e:
            print(f"Warning: Could not load state: {e}")
            return False

    def reset_thread(self) -> Optional[str]:
        """Create a new thread, discarding the old one."""
        self.thread_id = self._create_thread()
        if self.thread_id and self.persist:
            self._save_state()
        return self.thread_id

    def _get_or_create_assistant(self) -> Optional[str]:
        """Get existing assistant or create a new one."""
        # List existing assistants
        result = self._backboard_request("GET", "/assistants")
        # API returns a list directly
        assistants = result if isinstance(result, list) else result.get("assistants", []) if result else []
        for assistant in assistants:
            if assistant.get("name") == self.DEFAULT_ASSISTANT_NAME:
                print(f"EmbeddingStore: Found existing assistant")
                return assistant.get("assistant_id") or assistant.get("id")

        # Create new assistant
        result = self._backboard_request("POST", "/assistants", json_data={
            "name": self.DEFAULT_ASSISTANT_NAME,
            "description": "AMPM Meeting Memory - stores and retrieves meeting decisions",
            "llm_provider": self.DEFAULT_LLM_PROVIDER,
            "model": self.DEFAULT_MODEL
        })
        if result:
            assistant_id = result.get("assistant_id") or result.get("id")
            if assistant_id:
                print(f"EmbeddingStore: Created new assistant")
                return assistant_id

        return None

    def _create_thread(self) -> Optional[str]:
        """Create a new conversation thread."""
        if not self.assistant_id:
            return None

        result = self._backboard_request(
            "POST",
            f"/assistants/{self.assistant_id}/threads",
            json_data={}
        )
        if result and "thread_id" in result:
            return result["thread_id"]
        return None

    def add_to_backboard(self, doc_id: str, content: str, metadata: dict) -> bool:
        """
        Add a document to Backboard memory.

        Stores the content as a message with send_to_llm=false so it's
        saved to memory without generating a response.
        """
        if not self.thread_id:
            return False

        # Format content with metadata for better retrieval
        formatted_content = f"[{metadata.get('source', 'document')}:{doc_id}] {content}"

        result = self._backboard_request(
            "POST",
            f"/threads/{self.thread_id}/messages",
            form_data={
                "content": formatted_content,
                "send_to_llm": "false",
                "memory": "Auto",
                "metadata": json.dumps(metadata)
            }
        )
        return result is not None and result.get("status") == "COMPLETED"

    def search_backboard(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        Search documents via Backboard's memory-augmented RAG.

        Sends a query and uses the retrieved_memories from the response.
        """
        if not self.thread_id:
            return []

        result = self._backboard_request(
            "POST",
            f"/threads/{self.thread_id}/messages",
            form_data={
                "content": f"Search for: {query}",
                "llm_provider": self.DEFAULT_LLM_PROVIDER,
                "model_name": self.DEFAULT_MODEL,
                "memory": "Readonly",  # Search only, don't store this query
                "send_to_llm": "false"  # Just retrieve memories, no LLM response
            }
        )

        if not result:
            return []

        # Extract retrieved memories
        memories = result.get("retrieved_memories") or []
        return [
            SearchResult(
                id=m.get("id", ""),
                content=m.get("memory", ""),
                score=m.get("score", 0.0),
                metadata={},
                source="backboard_memory"
            )
            for m in memories[:top_k]
        ]

    def query_with_context(self, query: str) -> tuple[str, list[SearchResult]]:
        """
        Query Backboard with full RAG: retrieves memories and generates response.

        Returns:
            Tuple of (answer, retrieved_memories)
        """
        if not self.thread_id:
            return ("", [])

        result = self._backboard_request(
            "POST",
            f"/threads/{self.thread_id}/messages",
            form_data={
                "content": query,
                "llm_provider": self.DEFAULT_LLM_PROVIDER,
                "model_name": self.DEFAULT_MODEL,
                "memory": "Auto"
            }
        )

        if not result:
            return ("", [])

        answer = result.get("content", "")
        memories = result.get("retrieved_memories") or []

        search_results = [
            SearchResult(
                id=m.get("id", ""),
                content=m.get("memory", ""),
                score=m.get("score", 0.0),
                metadata={},
                source="backboard_memory"
            )
            for m in memories
        ]

        return (answer, search_results)

    # ==================== Local Fallback ====================

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI."""
        if not LOCAL_AVAILABLE or not self._openai:
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
        if not LOCAL_AVAILABLE or not self._openai:
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
