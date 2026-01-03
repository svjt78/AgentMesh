"""
Memory Manager

Manages long-term memory storage and retrieval beyond individual sessions.
Supports reactive and proactive memory retrieval patterns.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

from app.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """Memory entry for long-term storage"""

    memory_id: str
    created_at: str
    memory_type: str  # "session_conclusion", "insight", "user_preference", "fact"
    content: str
    metadata: Dict[str, Any]
    expires_at: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MemoryManager:
    """
    Manages long-term memory storage and retrieval.

    Memory enables agents to recall information from past sessions,
    creating continuity across workflows.
    """

    def __init__(self, storage_path: str = "storage/memory"):
        """
        Initialize the memory manager.

        Args:
            storage_path: Path to memory storage directory
        """
        self.config = get_config()
        self.storage_path = Path(storage_path)
        self.memories_file = self.storage_path / "memories.jsonl"
        self.index_file = self.storage_path / "index.json"

        # Create storage directory if it doesn't exist
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure storage directory and files exist"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Create index if it doesn't exist
            if not self.index_file.exists():
                with open(self.index_file, "w") as f:
                    json.dump({"version": "1.0.0", "keywords": {}, "tags": {}}, f, indent=2)

            # Create memories file if it doesn't exist
            if not self.memories_file.exists():
                self.memories_file.touch()

            logger.info(f"Memory storage initialized at {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to initialize memory storage: {e}", exc_info=True)
            raise

    def store_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any],
        tags: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """
        Store a new memory.

        Args:
            memory_type: Type of memory (session_conclusion, insight, etc.)
            content: Memory content (human-readable text)
            metadata: Additional structured metadata
            tags: Optional tags for categorization
            expires_in_days: Optional expiration in days (uses config default if None)

        Returns:
            memory_id: Unique identifier for the stored memory
        """
        # Generate memory ID
        memory_id = f"mem_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Calculate expiration
        expires_at = None
        if expires_in_days is None:
            # Use config default
            retention_days = self.config.memory.retention_days if hasattr(self.config, 'memory') else 90
            expires_in_days = retention_days

        if expires_in_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat() + "Z"

        # Create memory
        memory = Memory(
            memory_id=memory_id,
            created_at=datetime.utcnow().isoformat() + "Z",
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            expires_at=expires_at,
            tags=tags or [],
        )

        # Write to JSONL file
        try:
            with open(self.memories_file, "a") as f:
                f.write(json.dumps(asdict(memory)) + "\n")

            # Update index
            self._update_index(memory)

            logger.info(
                f"Memory stored: {memory_id}, type={memory_type}, "
                f"expires_at={expires_at}"
            )

            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}", exc_info=True)
            raise

    def retrieve_memories(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        mode: str = "reactive",
    ) -> List[Memory]:
        """
        Retrieve memories matching criteria.

        Args:
            query: Optional keyword query (searches content and metadata)
            memory_type: Optional filter by memory type
            tags: Optional filter by tags
            limit: Maximum number of memories to return
            mode: Retrieval mode ("reactive" or "proactive")

        Returns:
            List of matching Memory objects
        """
        try:
            all_memories = self._load_all_memories()

            # Apply expiration filter
            now = datetime.utcnow()
            valid_memories = []
            for memory in all_memories:
                if memory.expires_at:
                    try:
                        expires_at = datetime.fromisoformat(memory.expires_at.replace("Z", "+00:00"))
                        if expires_at.replace(tzinfo=None) < now:
                            continue  # Skip expired memories
                    except Exception:
                        pass  # Include if can't parse expiration
                valid_memories.append(memory)

            # Apply filters
            filtered = valid_memories

            if memory_type:
                filtered = [m for m in filtered if m.memory_type == memory_type]

            if tags:
                filtered = [m for m in filtered if any(tag in m.tags for tag in tags)]

            if query:
                # Simple keyword search (case-insensitive)
                query_lower = query.lower()
                filtered = [
                    m
                    for m in filtered
                    if query_lower in m.content.lower()
                    or query_lower in json.dumps(m.metadata).lower()
                ]

            # Sort by creation time (most recent first)
            filtered.sort(key=lambda m: m.created_at, reverse=True)

            # Apply limit
            result = filtered[:limit]

            logger.info(
                f"Retrieved {len(result)} memories (mode={mode}, "
                f"query={query}, type={memory_type}, tags={tags})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory object if found, None otherwise
        """
        try:
            all_memories = self._load_all_memories()
            for memory in all_memories:
                if memory.memory_id == memory_id:
                    return memory
            return None
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}", exc_info=True)
            return None

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Note: This rewrites the entire JSONL file without the deleted memory.

        Args:
            memory_id: Memory identifier to delete

        Returns:
            True if deleted, False if not found or error
        """
        try:
            all_memories = self._load_all_memories()

            # Filter out the memory to delete
            remaining = [m for m in all_memories if m.memory_id != memory_id]

            if len(remaining) == len(all_memories):
                logger.warning(f"Memory {memory_id} not found for deletion")
                return False

            # Rewrite file
            with open(self.memories_file, "w") as f:
                for memory in remaining:
                    f.write(json.dumps(asdict(memory)) + "\n")

            # Rebuild index
            self._rebuild_index(remaining)

            logger.info(f"Memory deleted: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
            return False

    def apply_retention_policy(self) -> int:
        """
        Apply retention policy to delete expired memories.

        Returns:
            Number of memories deleted
        """
        try:
            all_memories = self._load_all_memories()
            now = datetime.utcnow()

            # Filter out expired memories
            valid_memories = []
            deleted_count = 0

            for memory in all_memories:
                if memory.expires_at:
                    try:
                        expires_at = datetime.fromisoformat(memory.expires_at.replace("Z", "+00:00"))
                        if expires_at.replace(tzinfo=None) < now:
                            deleted_count += 1
                            logger.debug(f"Expired memory removed: {memory.memory_id}")
                            continue
                    except Exception:
                        pass  # Keep if can't parse
                valid_memories.append(memory)

            if deleted_count > 0:
                # Rewrite file with valid memories only
                with open(self.memories_file, "w") as f:
                    for memory in valid_memories:
                        f.write(json.dumps(asdict(memory)) + "\n")

                # Rebuild index
                self._rebuild_index(valid_memories)

                logger.info(f"Retention policy applied: {deleted_count} expired memories deleted")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}", exc_info=True)
            return 0

    def list_all_memories(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Memory]:
        """
        List all non-expired memories with pagination.

        Args:
            limit: Maximum number of memories to return (None = all)
            offset: Number of memories to skip

        Returns:
            List of Memory objects
        """
        try:
            all_memories = self._load_all_memories()

            # Filter expired
            now = datetime.utcnow()
            valid_memories = []
            for memory in all_memories:
                if memory.expires_at:
                    try:
                        expires_at = datetime.fromisoformat(memory.expires_at.replace("Z", "+00:00"))
                        if expires_at.replace(tzinfo=None) < now:
                            continue
                    except Exception:
                        pass
                valid_memories.append(memory)

            # Sort by creation time (most recent first)
            valid_memories.sort(key=lambda m: m.created_at, reverse=True)

            # Apply pagination
            if limit:
                return valid_memories[offset : offset + limit]
            else:
                return valid_memories[offset:]

        except Exception as e:
            logger.error(f"Failed to list memories: {e}", exc_info=True)
            return []

    def retrieve_memories_by_similarity(
        self,
        query_text: str,
        limit: int = 5,
        threshold: float = 0.7,
        use_embeddings: bool = False,
    ) -> List[tuple[Memory, float]]:
        """
        Retrieve memories by semantic similarity to query.

        Phase 8: Proactive memory preloading using similarity search.

        Args:
            query_text: Text to find similar memories for
            limit: Maximum number of memories to return
            threshold: Minimum similarity score (0-1)
            use_embeddings: If True, use embedding-based similarity (requires OpenAI API)

        Returns:
            List of (Memory, similarity_score) tuples, sorted by similarity
        """
        try:
            all_memories = self._load_all_memories()

            # Filter expired memories
            now = datetime.utcnow()
            valid_memories = []
            for memory in all_memories:
                if memory.expires_at:
                    try:
                        expires_at = datetime.fromisoformat(memory.expires_at.replace("Z", "+00:00"))
                        if expires_at.replace(tzinfo=None) < now:
                            continue  # Skip expired
                    except Exception:
                        pass
                valid_memories.append(memory)

            if not valid_memories:
                return []

            # Compute similarity scores
            scored_memories = []

            if use_embeddings:
                # Embedding-based similarity (requires OpenAI API)
                try:
                    scored_memories = self._compute_embedding_similarity(
                        query_text, valid_memories
                    )
                except Exception as e:
                    logger.warning(
                        f"Embedding similarity failed, falling back to keyword: {e}"
                    )
                    scored_memories = self._compute_keyword_similarity(
                        query_text, valid_memories
                    )
            else:
                # Keyword-based similarity (faster, no API required)
                scored_memories = self._compute_keyword_similarity(
                    query_text, valid_memories
                )

            # Filter by threshold
            scored_memories = [
                (mem, score) for mem, score in scored_memories if score >= threshold
            ]

            # Sort by similarity (descending)
            scored_memories.sort(key=lambda x: x[1], reverse=True)

            # Apply limit
            result = scored_memories[:limit]

            logger.info(
                f"Similarity search: {len(result)} memories found "
                f"(query_length={len(query_text)}, threshold={threshold})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to retrieve memories by similarity: {e}", exc_info=True)
            return []

    # ============= Private Helpers =============

    def _load_all_memories(self) -> List[Memory]:
        """Load all memories from JSONL file"""
        memories = []
        try:
            if not self.memories_file.exists():
                return []

            with open(self.memories_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        memory = Memory(**data)
                        memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"Failed to load memories: {e}", exc_info=True)
            return []

    def _update_index(self, memory: Memory) -> None:
        """Update keyword and tag index for faster searches"""
        try:
            # Load existing index
            with open(self.index_file, "r") as f:
                index = json.load(f)

            # Update tag index
            for tag in memory.tags:
                if tag not in index["tags"]:
                    index["tags"][tag] = []
                if memory.memory_id not in index["tags"][tag]:
                    index["tags"][tag].append(memory.memory_id)

            # Update keyword index (simple: split content into words)
            words = memory.content.lower().split()
            for word in words:
                if len(word) > 3:  # Only index words longer than 3 chars
                    if word not in index["keywords"]:
                        index["keywords"][word] = []
                    if memory.memory_id not in index["keywords"][word]:
                        index["keywords"][word].append(memory.memory_id)

            # Write updated index
            with open(self.index_file, "w") as f:
                json.dump(index, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update index: {e}", exc_info=True)

    def _rebuild_index(self, memories: List[Memory]) -> None:
        """Rebuild entire index from memories"""
        try:
            index = {"version": "1.0.0", "keywords": {}, "tags": {}}

            for memory in memories:
                # Tags
                for tag in memory.tags:
                    if tag not in index["tags"]:
                        index["tags"][tag] = []
                    if memory.memory_id not in index["tags"][tag]:
                        index["tags"][tag].append(memory.memory_id)

                # Keywords
                words = memory.content.lower().split()
                for word in words:
                    if len(word) > 3:
                        if word not in index["keywords"]:
                            index["keywords"][word] = []
                        if memory.memory_id not in index["keywords"][word]:
                            index["keywords"][word].append(memory.memory_id)

            with open(self.index_file, "w") as f:
                json.dump(index, f, indent=2)

            logger.info("Index rebuilt successfully")

        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}", exc_info=True)

    def _compute_keyword_similarity(
        self, query_text: str, memories: List[Memory]
    ) -> List[tuple[Memory, float]]:
        """
        Compute keyword-based similarity using TF-IDF style scoring.

        Fast, no API required. Good baseline for similarity search.
        """
        import re
        from collections import Counter

        # Tokenize query (simple word splitting)
        query_words = set(re.findall(r'\w+', query_text.lower()))
        query_words = {w for w in query_words if len(w) > 2}  # Filter short words

        if not query_words:
            return [(m, 0.0) for m in memories]

        scored_memories = []

        for memory in memories:
            # Tokenize memory content
            memory_text = memory.content.lower()
            memory_words = set(re.findall(r'\w+', memory_text))
            memory_words = {w for w in memory_words if len(w) > 2}

            if not memory_words:
                scored_memories.append((memory, 0.0))
                continue

            # Compute Jaccard similarity (simple but effective)
            intersection = query_words & memory_words
            union = query_words | memory_words

            if not union:
                similarity = 0.0
            else:
                similarity = len(intersection) / len(union)

            # Boost score if query words appear in tags
            tag_boost = 0.0
            if memory.tags:
                tag_words = {tag.lower() for tag in memory.tags}
                tag_matches = query_words & tag_words
                tag_boost = len(tag_matches) * 0.1  # 10% boost per matching tag

            final_score = min(1.0, similarity + tag_boost)
            scored_memories.append((memory, final_score))

        return scored_memories

    def _compute_embedding_similarity(
        self, query_text: str, memories: List[Memory]
    ) -> List[tuple[Memory, float]]:
        """
        Compute embedding-based similarity using OpenAI embeddings API.

        More accurate than keyword-based, but requires API key and costs $.
        """
        try:
            from openai import OpenAI

            # Get OpenAI client
            api_key = self.config.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")

            client = OpenAI(api_key=api_key)

            # Generate query embedding
            query_response = client.embeddings.create(
                model="text-embedding-ada-002", input=query_text
            )
            query_embedding = query_response.data[0].embedding

            # Generate memory embeddings and compute cosine similarity
            scored_memories = []

            for memory in memories:
                # Use content as embedding input
                memory_response = client.embeddings.create(
                    model="text-embedding-ada-002", input=memory.content
                )
                memory_embedding = memory_response.data[0].embedding

                # Compute cosine similarity
                similarity = self._cosine_similarity(query_embedding, memory_embedding)
                scored_memories.append((memory, similarity))

            return scored_memories

        except ImportError:
            logger.error("OpenAI package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Embedding similarity computation failed: {e}")
            raise

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math

        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get singleton MemoryManager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
