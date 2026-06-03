"""
FastAPI entry point for the DocQA Assistant.

Routes all requests through the Google ADK agent tree:
  orchestrator → classify_intents → ingestion/retrieval/answering agents

Run:
  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --log-level debug
"""

import uuid
import os
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import requests as http_requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
    DocumentListResponse,
    ErrorResponse,
)
from app.services.file_service import save_upload_file
from app.services.document_registry import document_registry
from app.services.ollama_model_service import (
    OllamaModelCapabilityError,
    assert_ollama_model_supports_adk_tools,
    build_tool_support_error,
    is_ollama_tool_support_error,
)

# ── Ollama/LiteLLM runtime timeout guard ─────────────────────
# Google ADK routes agent model calls through LiteLLM. These environment
# defaults keep slow local Ollama models from being cancelled prematurely while
# preserving quick startup and health checks via the dedicated settings above.
os.environ.setdefault("OLLAMA_REQUEST_TIMEOUT", str(settings.ollama_request_timeout))
os.environ.setdefault("LITELLM_REQUEST_TIMEOUT", str(settings.ollama_request_timeout))
os.environ.setdefault("LITELLM_TIMEOUT", str(settings.ollama_request_timeout))

# ── ADK imports ──────────────────────────────────────────────
from app.adk_runtime.orchestrator import orchestrator, classify_intents
from app.adk_runtime.retrieval_agent import retrieve_chunks
from app.adk_runtime.answering_agent import generate_answer
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.config import settings
import litellm

os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

# Pass API key to LiteLLM for Ollama Cloud
os.environ["OLLAMA_API_KEY"] = settings.ollama_api_key

# Tell LiteLLM where Ollama is
litellm.api_base = settings.ollama_base_url

# ── Pass Ollama API key to LiteLLM ──
os.environ["OLLAMA_API_KEY"] = settings.ollama_api_key
print(f"DEBUG: OLLAMA_API_KEY = '{settings.ollama_api_key[:5]}...'")

from dotenv import load_dotenv
load_dotenv()

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Batching embeddings function ─────────────────────────────────────────
def batch_embeddings(texts, batch_size=None):
    """
    Generate embeddings in small batches to avoid Ollama request timeouts.
    """
    from app.tools.ollama_client import ollama_embed

    if batch_size is None:
        batch_size = settings.ollama_embed_batch_size

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(
            "Embedding batch %s-%s of %s",
            i + 1,
            min(i + batch_size, len(texts)),
            len(texts),
        )
        embeddings = ollama_embed(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings

# ── ADK Runner — executes the agent tree ─────────────────────
runner = InMemoryRunner(agent=orchestrator, app_name="docqa_assistant")


# ── Lifespan (MUST be defined BEFORE FastAPI) ────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: check Ollama connectivity. Shutdown: log graceful exit."""
    # ── STARTUP ──
    try:
        resp = http_requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=settings.ollama_startup_check_timeout,
        )
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        logger.info("Ollama is reachable. Available models: %s", models)
        try:
            assert_ollama_model_supports_adk_tools()
            logger.info(
                "Ollama chat model %s supports ADK tool/function calling.",
                settings.ollama_chat_model,
            )
        except OllamaModelCapabilityError as model_exc:
            logger.warning("%s", model_exc)
    except Exception as exc:
        logger.warning(
            "Ollama is NOT reachable at %s — %s. "
            "Ensure Ollama is running before making requests.",
            settings.ollama_base_url,
            exc,
        )
    yield
    # ── SHUTDOWN ──
    logger.info("Shutting down DocQA Assistant gracefully...")


# ── FastAPI app ──────────────────────────────────────────────
app = FastAPI(
    title="Google ADK + Ollama Document Q&A Assistant",
    version="2.0.0",
    responses={400: {"model": ErrorResponse}},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# HELPER — Run a message through the ADK agent tree
# ═══════════════════════════════════════════════════════════════

async def _run_agent(user_id: str, message: str) -> dict:
    """Send a message through the ADK orchestrator and collect the final response."""

    try:
        assert_ollama_model_supports_adk_tools()
    except OllamaModelCapabilityError as exc:
        logger.warning("ADK tool-capability validation failed for user=%s: %s", user_id, exc)
        raise HTTPException(status_code=424, detail=str(exc))
    except http_requests.RequestException as exc:
        logger.exception("Ollama model capability check failed for user=%s", user_id)
        raise HTTPException(
            status_code=503,
            detail=f"Unable to validate Ollama chat model '{settings.ollama_chat_model}': {exc}",
        )

    # Step 1: Create session FIRST (required by InMemoryRunner)
    session = await runner.session_service.create_session(
        app_name="docqa_assistant",
        user_id=user_id,
    )

    # Step 2: Build the message
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    # Step 3: Run with the created session's ID
    final_answer = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        text = part.text.strip()
                        # DEBUG — log everything
                        logger.info(
                            "EVENT author=%s | text_preview=%s",
                            getattr(event, "author", "unknown"),
                            text[:150]
                        )
                        final_answer = text  # Keep updating final_answer until the end of the stream
    except Exception as exc:
        if is_ollama_tool_support_error(exc):
            detail = build_tool_support_error(settings.ollama_chat_model)
            logger.warning(
                "Ollama rejected ADK tool/function calling for model %s: %s",
                settings.ollama_chat_model,
                detail,
            )
            raise HTTPException(status_code=424, detail=detail)

        logger.exception("ADK runner error for user=%s", user_id)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}")

    return {"answer": final_answer, "session_id": session.id}


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

# ── Health check ─────────────────────────────────────────────
@app.get("/health")
def health():
    """Health check endpoint.
    
    Returns:
        dict with:
        - status: "ok" if API is operational
        - ollama_status: "ok" if Ollama is reachable, "down" otherwise
        - timestamp: ISO timestamp
    """
    ollama_status = "down"
    
    # ✓ Check if Ollama is actually reachable
    try:
        resp = http_requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=settings.ollama_health_check_timeout,
        )
        if resp.status_code == 200:
            ollama_status = "ok"
            logger.debug("Ollama health check passed")
        else:
            logger.warning(f"Ollama returned status code {resp.status_code}")
    except http_requests.Timeout:
        logger.warning("Ollama health check timed out")
    except http_requests.ConnectionError as e:
        logger.warning(f"Ollama connection error: {e}")
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
    
    return {
        "status": "ok",
        "ollama_status": ollama_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Upload document ──────────────────────────────────────────
@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(default="default"),
):
    # Step 1: Save file to disk
    try:
        saved = await save_upload_file(file=file, user_id=user_id)
    except ValueError as exc:
        error_msg = str(exc)
        if "Unsupported file type" in error_msg:
            raise HTTPException(status_code=415, detail=error_msg)
        if "exceeds max size" in error_msg:
            raise HTTPException(status_code=413, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    # Step 2: Run ingestion DIRECTLY (skip ADK agent for uploads)
    # This gives us the actual structured result with chunk_count
    try:
        from app.tools.extract_text import extract_text
        from app.tools.chunk_text import chunk_text
        from app.tools.ollama_client import ollama_embed
        from app.tools.vector_store import vector_store

        document_id = document_registry.create_document(
            user_id=user_id,
            document_name=saved["file_name"],
            file_type=saved["file_type"],
            status="processing",
        )

        text_units = extract_text(
            file_path=saved["file_path"],
            file_type=saved["file_type"],
        )

        chunks = chunk_text(text_units=text_units)

        if chunks:
            embeddings = batch_embeddings([c["text"] for c in chunks])
            vector_store.add_chunks(
                document_id=document_id,
                document_name=saved["file_name"],
                user_id=user_id,
                chunks=chunks,
                embeddings=embeddings,
            )

        document_registry.update_document(
            document_id,
            status="indexed",
            chunk_count=len(chunks),
        )

        return UploadResponse(
            document_id=document_id,
            document_name=saved["file_name"],
            file_type=saved["file_type"],
            status="indexed",
            chunk_count=len(chunks),
            message=f"Successfully indexed {len(chunks)} chunks from {saved['file_name']}.",
        )

    except ValueError as exc:
        logger.exception("Ingestion validation failed for %s", saved["file_name"])
        detail = str(exc)
        if "document_id" in locals():
            document_registry.update_document(document_id, status="failed", error=detail)
        status_code = 409 if "Embedding dimension mismatch" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as exc:
        logger.exception("Ingestion failed for %s", saved["file_name"])
        if "document_id" in locals():
            document_registry.update_document(document_id, status="failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

# ── Chat / Query ─────────────────────────────────────────────
@app.post("/chat/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """Answer a document question with a reliable grounded pipeline.

    The endpoint uses the same ADK tool functions as the agents, but executes
    retrieval and answer generation directly so the API always returns stable
    JSON (`answer`, `citations`, `metadata`) to the React client. This avoids UI
    crashes caused by raw ADK text/tool events while keeping the agent codepath
    available for ADK runtimes.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    message = request.message.strip()
    intent_result = classify_intents(message)
    intent = "summary" if "summary" in intent_result.get("intents", []) else "qa"
    document_id = request.document_id or (
        document_registry.latest_document_id(request.user_id) if request.use_latest else None
    ) or "all"

    try:
        retrieved = retrieve_chunks(
            query=message,
            user_id=request.user_id,
            document_id=document_id,
            intent=intent,
        )
        answer_result = generate_answer(
            question=message,
            chunks=json.dumps(retrieved.get("chunks", [])),
            intent=intent,
        )
    except ValueError as exc:
        logger.exception("Query validation failed for user=%s", request.user_id)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Query failed for user=%s", request.user_id)
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

    return QueryResponse(
        answer=answer_result.get("answer", ""),
        citations=answer_result.get("citations", []),
        metadata={
            "status": answer_result.get("status", retrieved.get("status")),
            "intent": intent,
            "retrieved_count": retrieved.get("chunk_count", 0),
            "document_id": None if document_id == "all" else document_id,
            "retrieval_status": retrieved.get("status"),
        },
    )


# ── List documents ───────────────────────────────────────────
@app.get("/documents/list", response_model=DocumentListResponse)
def list_documents(user_id: str = "default"):
    """List all documents uploaded by a user."""
    docs = document_registry.list_documents(user_id)
    return DocumentListResponse(user_id=user_id, documents=docs)


# ── Delete document ──────────────────────────────────────────
@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """Delete a document from vector store and registry."""
    try:
        from app.tools.vector_store import vector_store
        vector_store.delete_document(document_id)
        document_registry.delete_document(document_id)
        return {"status": "deleted", "document_id": document_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Delete failed for %s", document_id)
        raise HTTPException(status_code=500, detail=str(exc))
