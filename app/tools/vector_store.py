"""
ChromaDB vector store wrapper.
Uses cosine distance metric (recommended for embedding similarity).
Includes document deletion support.
"""

import uuid
import logging
import chromadb

from app.config import settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},  # Cosine distance
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
            self.collection.add(
                ids=ids,
                documents=docs,
                embeddings=embeddings,
                metadatas=metas,
            )
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
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

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

    # ── Delete all chunks for a document ─────────────────────
    def delete_document(self, document_id: str):
        """Remove all chunks belonging to a document."""
        self.collection.delete(
            where={"document_id": document_id},
        )
        logger.info("Deleted all chunks for document %s", document_id)


vector_store = ChromaVectorStore()
