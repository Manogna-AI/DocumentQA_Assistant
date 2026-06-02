"""
In-memory document metadata registry.
Production: replace with PostgreSQL / SQLite.
"""

import uuid
from datetime import datetime, timezone


class InMemoryDocumentRegistry:
    def __init__(self):
        self.documents: dict[str, dict] = {}

    # ── Create ───────────────────────────────────────────────
    def create_document(
        self,
        user_id: str,
        document_name: str,
        file_type: str,
        status: str,
    ) -> str:
        document_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self.documents[document_id] = {
            "document_id": document_id,
            "user_id": user_id,
            "document_name": document_name,
            "file_type": file_type,
            "status": status,
            "chunk_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        return document_id

    # ── Update ───────────────────────────────────────────────
    def update_document(self, document_id: str, **updates):
        if document_id not in self.documents:
            raise ValueError(f"Document {document_id} not found")
        self.documents[document_id].update(updates)
        self.documents[document_id]["updated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

    # ── Get single document ──────────────────────────────────
    def get_document(self, document_id: str) -> dict | None:
        return self.documents.get(document_id)

    # ── List all documents for a user ────────────────────────
    def list_documents(self, user_id: str) -> list[dict]:
        return sorted(
            [d for d in self.documents.values() if d["user_id"] == user_id],
            key=lambda d: d["created_at"],
            reverse=True,
        )

    # ── Latest indexed document for a user ───────────────────
    def latest_document_id(self, user_id: str) -> str | None:
        user_docs = [
            d
            for d in self.documents.values()
            if d["user_id"] == user_id and d["status"] == "indexed"
        ]
        if not user_docs:
            return None
        return sorted(
            user_docs, key=lambda d: d["created_at"], reverse=True
        )[0]["document_id"]

    # ── List all indexed document IDs for a user ─────────────
    def indexed_document_ids(self, user_id: str) -> list[str]:
        return [
            d["document_id"]
            for d in self.documents.values()
            if d["user_id"] == user_id and d["status"] == "indexed"
        ]

    # ── Delete ───────────────────────────────────────────────
    def delete_document(self, document_id: str):
        if document_id not in self.documents:
            raise ValueError(f"Document {document_id} not found")
        del self.documents[document_id]


document_registry = InMemoryDocumentRegistry()
