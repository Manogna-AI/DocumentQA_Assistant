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

def retrieve_chunks(
    query: str,
    user_id: str = "default",
    document_id: str = "latest",
    intent: str = "qa",
) -> dict:
    """Embed the user query via Ollama and perform top-K similarity
    search over indexed document chunks in ChromaDB.

    Args:
        query: The user's question or search text.
        user_id: ID of the user. If the exact user has no documents,
                 falls back to 'default' user.
        document_id: ID of the target document. Use 'latest' or 'all'
                     to search across all documents for the user.
        intent: 'qa' for focused retrieval (top 12),
                'summary' for broader retrieval (top 30).

    Returns:
        dict with status, chunk_count, and list of text excerpts
        with page/slide metadata and similarity scores.
    """

    top_k = settings.top_k_summary if intent == "summary" else settings.top_k_initial

    # Embed query
    query_embedding = ollama_embed([query])[0]

    # ── Handle document_id = "latest" or "all" ──
    # Search without document_id filter to find ANY matching chunks
    search_specific = document_id not in ("latest", "all", "")

    if search_specific:
        # Search specific document
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"user_id": user_id, "document_id": document_id},
        )

        # Fallback: try with user_id="default" if no results
        if not results and user_id != "default":
            results = vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters={"user_id": "default", "document_id": document_id},
            )
    else:
        # Search across ALL documents for this user
        results = _search_all_documents(
            vector_store, query_embedding, top_k, user_id
        )

        # Fallback: try with user_id="default"
        if not results and user_id != "default":
            results = _search_all_documents(
                vector_store, query_embedding, top_k, "default"
            )

    # Filter by minimum similarity score
    filtered = [
        r for r in results
        if r.get("score", 0.0) >= settings.min_similarity_score
    ]
    # NEW: Log before limiting
    logger.info(f"Retrieved {len(filtered)} chunks before limiting")

    # NEW: ✓ Hard limit — prevents LLM overload / crash (using config)
    filtered = filtered[:settings.qa_max_chunk_count]

    # NEW: Log after limiting
    logger.info(f"Using {len(filtered)} chunks after limiting")


    return {
        "status": "success" if filtered else "no_results",
        "chunk_count": len(filtered),
        "chunks": filtered,
        "message": f"Retrieved {len(filtered)} relevant chunks (intent={intent}).",
    }


def _search_all_documents(vector_store, query_embedding, top_k, user_id):
    """Search across all documents for a user (no document_id filter)."""
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
            })
        return output
    except Exception as e:
        logger.error("Error in _search_all_documents: %s", e)
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