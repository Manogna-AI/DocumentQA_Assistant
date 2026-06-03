"""
Agent 2: Retrieval Agent
Tools: ollama_embed → vector_store.search
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
from app.config import settings
from google.adk.agents import Agent
from app.tools.ollama_client import ollama_embed
from app.tools.vector_store import vector_store
from .answering_agent import answering_agent

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_base_url)
MODEL = f"ollama_chat/{settings.ollama_chat_model}"
#MODEL = "gemini-2.0-flash"

# ── Tool: Uses ollama_embed + vector_store.search ──

def _normalize_result(result: dict, source: str) -> dict:
    """Normalize retrieval metadata and annotate the retrieval source."""
    normalized = dict(result)
    metadata = dict(normalized.get("metadata") or {})
    normalized["metadata"] = metadata
    normalized["retrieval_source"] = normalized.get("retrieval_source", source)
    normalized["score"] = float(normalized.get("score") or 0.0)
    return normalized


def _merge_ranked_results(semantic_results: list[dict], keyword_results: list[dict]) -> list[dict]:
    """Merge semantic and keyword hits by chunk ID, preserving best scores."""
    merged: dict[str, dict] = {}

    for item in semantic_results:
        normalized = _normalize_result(item, "semantic")
        chunk_id = normalized.get("chunk_id")
        if not chunk_id:
            continue
        normalized["semantic_score"] = normalized["score"]
        normalized["hybrid_score"] = normalized["score"]
        merged[chunk_id] = normalized

    for item in keyword_results:
        normalized = _normalize_result(item, "keyword")
        chunk_id = normalized.get("chunk_id")
        if not chunk_id:
            continue
        keyword_score = float(normalized.get("keyword_score") or normalized.get("score") or 0.0)
        if chunk_id in merged:
            existing = merged[chunk_id]
            existing["keyword_score"] = keyword_score
            existing["retrieval_source"] = "hybrid"
            existing["hybrid_score"] = max(existing.get("hybrid_score", 0.0), keyword_score)
            existing["score"] = max(existing.get("score", 0.0), keyword_score)
        else:
            normalized["keyword_score"] = keyword_score
            normalized["hybrid_score"] = keyword_score
            merged[chunk_id] = normalized

    return sorted(merged.values(), key=lambda item: item.get("hybrid_score", item.get("score", 0.0)), reverse=True)


def retrieve_chunks(
    query: str,
    user_id: str = "default",
    document_id: str = "latest",
    intent: str = "qa",
) -> dict:
    """Retrieve relevant chunks using hybrid semantic + keyword search.

    Exact keyword overlap is merged with embedding similarity so answers stay
    grounded when the user asks about names, dates, clauses, numbers, or terms
    that vector retrieval alone may under-rank.
    """

    top_k = settings.top_k_summary if intent == "summary" else settings.top_k_initial
    expanded_top_k = max(top_k * 3, settings.qa_max_chunk_count)
    search_specific = document_id not in ("latest", "all", "", None)

    def run_for_user(target_user_id: str) -> list[dict]:
        filters = {"user_id": target_user_id}
        if search_specific:
            filters["document_id"] = document_id

        semantic_results: list[dict] = []
        try:
            query_embedding = ollama_embed([query])[0]
            if search_specific:
                semantic_results = vector_store.search(
                    query_embedding=query_embedding,
                    top_k=expanded_top_k,
                    filters=filters,
                )
            else:
                semantic_results = _search_all_documents(
                    vector_store, query_embedding, expanded_top_k, target_user_id
                )
        except Exception as exc:
            logger.exception("Semantic retrieval failed; continuing with keyword search: %s", exc)

        keyword_results = vector_store.keyword_search(
            query=query,
            top_k=expanded_top_k,
            filters=filters,
        )
        return _merge_ranked_results(semantic_results, keyword_results)

    results = run_for_user(user_id)
    if not results and user_id != "default":
        results = run_for_user("default")

    filtered = [
        r for r in results
        if r.get("keyword_score", 0.0) > 0 or r.get("score", 0.0) >= settings.min_similarity_score
    ]
    logger.info("Retrieved %d hybrid chunks before limiting", len(filtered))

    filtered = filtered[:settings.qa_max_chunk_count]
    logger.info("Using %d chunks after limiting", len(filtered))

    return {
        "status": "success" if filtered else "no_results",
        "chunk_count": len(filtered),
        "chunks": filtered,
        "message": f"Retrieved {len(filtered)} relevant chunks (intent={intent}).",
    }


def _search_all_documents(vector_store, query_embedding, top_k, user_id):
    """Search semantically across all documents for a user (no document_id filter)."""
    try:
        result = vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        output = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        for doc, meta, distance, chunk_id in zip(docs, metas, distances, ids):
            score = 1.0 - (float(distance) / 2.0)
            output.append({
                "chunk_id": meta.get("chunk_id", chunk_id),
                "text": doc,
                "metadata": {
                    **meta,
                    "page_number": None if meta.get("page_number") == -1 else meta.get("page_number"),
                    "slide_number": None if meta.get("slide_number") == -1 else meta.get("slide_number"),
                },
                "score": score,
                "retrieval_source": "semantic",
            })
        return output
    except Exception as e:
        logger.exception("Error in _search_all_documents: %s", e)
        return []


# ── Agent Definition ──

retrieval_agent = Agent(
    name="retrieval_agent",
    model=MODEL,
    description=(
        "Retrieval Agent — Embeds the user query using the same Ollama embedding "
        "model, performs top-K similarity search over indexed chunks in ChromaDB, "
        "and returns relevant text snippets with page/slide metadata and scores. "
        "After retrieval, automatically transfers to answering_agent."
    ),
    instruction=(
        "/no_think\n"
        "You are the Retrieval Agent.\n\n"
        "WHEN TO ACT: When you need to find relevant document chunks.\n\n"
        "HOW TO ACT:\n"
        "1. Use the retrieve_chunks tool with the user's query\n"
        "2. Pass intent='summary' for summarization requests\n"
        "3. Pass intent='qa' for specific questions\n"
        "4. Return ALL retrieved chunks — the answering agent will use them\n\n"
        "════════════════════════════════════════\n"
        "AFTER RETRIEVAL — MANDATORY\n"
        "════════════════════════════════════════\n\n"
        "After retrieving chunks, you MUST transfer to answering_agent.\n"
        "NEVER return raw chunks to the user directly.\n"
        "ALWAYS transfer to answering_agent with the retrieved context.\n"
        "Do not modify the chunks.\n"
    ),
    tools=[retrieve_chunks],
    sub_agents=[answering_agent],        # ← ADD THIS
    output_key="retrieved_chunks",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)