"""
ChromaDB vector store wrapper.
Uses cosine distance metric (recommended for embedding similarity).
Includes document deletion support.
"""

import uuid
import hashlib
import logging
import re
import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

_DIMENSION_ERROR_PATTERN = re.compile(
    r"expecting embedding with dimension of (?P<expected>\d+), got (?P<received>\d+)",
    re.IGNORECASE,
)
_COLLECTION_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")
_MAX_COLLECTION_NAME_LENGTH = 63


def _tokenize_keyword_query(text: str) -> set[str]:
    """Return normalized keyword tokens suitable for lightweight lexical search."""
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
        "to", "was", "what", "when", "where", "which", "who", "why", "with",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{2,}", text.lower())
        if token not in stop_words
    }


def _sanitize_collection_part(value: str) -> str:
    normalized = _COLLECTION_NAME_PATTERN.sub("_", value.lower()).strip("._-")
    return normalized or "collection"


def _collection_name_for_model(base_name: str, embedding_model: str) -> str:
    """Build a Chroma-safe collection name scoped to the embedding model."""
    if not settings.chroma_scope_by_embedding_model:
        return _sanitize_collection_part(base_name)

    raw_name = (
        f"{_sanitize_collection_part(base_name)}_"
        f"{_sanitize_collection_part(embedding_model)}"
    )
    if len(raw_name) <= _MAX_COLLECTION_NAME_LENGTH:
        return raw_name

    digest = hashlib.sha1(raw_name.encode("utf-8")).hexdigest()[:8]
    keep = _MAX_COLLECTION_NAME_LENGTH - len(digest) - 1
    return f"{raw_name[:keep].rstrip('._-')}_{digest}"


def _dimension_error_message(exc: Exception, collection_name: str) -> str | None:
    """Return a user-actionable message for Chroma embedding dimension errors."""
    match = _DIMENSION_ERROR_PATTERN.search(str(exc))
    if not match:
        return None

    expected = match.group("expected")
    received = match.group("received")
    return (
        f"Embedding dimension mismatch for Chroma collection '{collection_name}': "
        f"the collection was created with {expected}-dimension embeddings, but "
        f"the configured Ollama embedding model '{settings.ollama_embedding_model}' "
        f"returned {received}-dimension embeddings. Use the same "
        "OLLAMA_EMBEDDING_MODEL that created the collection, or set "
        "CHROMA_COLLECTION_NAME to a new collection before indexing with a "
        "different embedding model."
    )


class ChromaVectorStore:
    def __init__(self):
        self.collection_name = _collection_name_for_model(
            settings.chroma_collection_name,
            settings.ollama_embedding_model,
        )
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": settings.ollama_embedding_model,
            },
        )
        self._expected_embedding_dim: int | None = None  # Track expected dimension

    # ── Add chunks ───────────────────────────────────────────
    def add_chunks(
        self,
        document_id: str,
        document_name: str,
        user_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
    ):
        """Add chunks with embeddings to the vector store.
        
        Args:
            document_id: Document identifier
            document_name: Human-readable document name
            user_id: User who uploaded the document
            chunks: List of text chunks with metadata
            embeddings: List of embedding vectors (must match chunk count)
            
        Raises:
            ValueError: If embeddings are invalid or mismatched
        """
        # ✓ VALIDATION 1: Embedding count matches chunk count
        if len(embeddings) != len(chunks):
            error_msg = (
                f"Embedding count mismatch: {len(embeddings)} embeddings "
                f"for {len(chunks)} chunks"
            )
            logger.error(f"[add_chunks] {error_msg}")
            raise ValueError(error_msg)
        
        if not embeddings:
            logger.warning(f"[add_chunks] No embeddings provided for document {document_id}")
            return
        
        # ✓ VALIDATION 2: All embeddings have same dimension
        embedding_dims = [len(e) for e in embeddings]
        if len(set(embedding_dims)) > 1:
            error_msg = (
                f"Inconsistent embedding dimensions: {set(embedding_dims)}. "
                f"All embeddings must have same dimension."
            )
            logger.error(f"[add_chunks] {error_msg}")
            raise ValueError(error_msg)
        
        current_dim = embedding_dims[0]
        
        # ✓ VALIDATION 3: Check embedding dimension on first use
        if self._expected_embedding_dim is None:
            self._expected_embedding_dim = current_dim
            logger.info(
                f"[add_chunks] Setting expected embedding dimension: {current_dim}"
            )
        elif current_dim != self._expected_embedding_dim:
            error_msg = (
                f"Embedding dimension mismatch: received {current_dim}, "
                f"expected {self._expected_embedding_dim}. "
                f"Check that all documents use the same embedding model."
            )
            logger.error(f"[add_chunks] {error_msg}")
            raise ValueError(error_msg)
        
        ids, docs, metas = [], [], []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            docs.append(chunk["text"])
            metas.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "document_name": document_name,
                "user_id": user_id,
                "chunk_index": chunk.get("chunk_index"),
                "page_number": chunk.get("page_number") or -1,
                "slide_number": chunk.get("slide_number") or -1,
                "section_title": chunk.get("section_title") or "",
                "source_type": chunk.get("source_type") or "",
            })
        
        if ids:
            try:
                self.collection.add(
                    ids=ids,
                    documents=docs,
                    embeddings=embeddings,
                    metadatas=metas,
                )
            except Exception as exc:
                dimension_message = _dimension_error_message(exc, self.collection_name)
                if dimension_message:
                    logger.error("[add_chunks] %s", dimension_message)
                    raise ValueError(dimension_message) from exc
                raise
            logger.info(
                f"[add_chunks] Stored {len(ids)} chunks for document {document_id} "
                f"(user={user_id}, embedding_dim={current_dim})"
            )

    # ── Search ───────────────────────────────────────────────
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict,
    ) -> list[dict]:
        where = {
            "$and": [
                {"user_id": filters["user_id"]},
                {"document_id": filters["document_id"]},
            ]
        }
        try:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            dimension_message = _dimension_error_message(exc, self.collection_name)
            if dimension_message:
                logger.error("[search] %s", dimension_message)
                raise ValueError(dimension_message) from exc
            raise

        output = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        for doc, meta, distance, chunk_id in zip(docs, metas, distances, ids):
            # Cosine distance in Chroma: 0 = identical, 2 = opposite
            # Convert to similarity: 1 - (distance / 2)
            score = 1.0 - (float(distance) / 2.0)
            output.append({
                "chunk_id": meta.get("chunk_id", chunk_id),
                "text": doc,
                "metadata": {
                    **meta,
                    "page_number": (
                        None if meta.get("page_number") == -1
                        else meta.get("page_number")
                    ),
                    "slide_number": (
                        None if meta.get("slide_number") == -1
                        else meta.get("slide_number")
                    ),
                },
                "score": score,
            })
        return output

    # ── Keyword Search ──────────────────────────────────────
    def keyword_search(
        self,
        query: str,
        top_k: int,
        filters: dict,
    ) -> list[dict]:
        """Search chunks lexically using keyword overlap.

        This complements vector similarity when embeddings miss exact names,
        clauses, numbers, or domain terms in uploaded documents.
        """
        query_terms = _tokenize_keyword_query(query)
        if not query_terms:
            return []

        where_terms = [{"user_id": filters["user_id"]}]
        document_id = filters.get("document_id")
        if document_id and document_id not in ("latest", "all"):
            where_terms.append({"document_id": document_id})
        where = {"$and": where_terms} if len(where_terms) > 1 else where_terms[0]

        result = self.collection.get(
            where=where,
            include=["documents", "metadatas"],
        )
        docs = result.get("documents", [])
        metas = result.get("metadatas", [])
        ids = result.get("ids", [])

        ranked = []
        for doc, meta, chunk_id in zip(docs, metas, ids):
            doc_terms = _tokenize_keyword_query(doc or "")
            overlap = query_terms & doc_terms
            if not overlap:
                continue
            # Blend exact overlap ratio with a small phrase bonus for stable ranking.
            score = min(1.0, len(overlap) / max(len(query_terms), 1))
            if query.lower() in (doc or "").lower():
                score = min(1.0, score + 0.2)
            ranked.append({
                "chunk_id": meta.get("chunk_id", chunk_id),
                "text": doc,
                "metadata": {
                    **meta,
                    "page_number": None if meta.get("page_number") == -1 else meta.get("page_number"),
                    "slide_number": None if meta.get("slide_number") == -1 else meta.get("slide_number"),
                },
                "score": score,
                "keyword_score": score,
                "retrieval_source": "keyword",
            })

        ranked.sort(key=lambda item: item["keyword_score"], reverse=True)
        return ranked[:top_k]

    # ── Delete all chunks for a document ─────────────────────
    def delete_document(self, document_id: str):
        """Remove all chunks belonging to a document."""
        self.collection.delete(
            where={"document_id": document_id},
        )
        logger.info("Deleted all chunks for document %s", document_id)


vector_store = ChromaVectorStore()
