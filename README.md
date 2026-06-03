# DocQA Assistant Backend

Production-oriented document question answering service built with **FastAPI**, **Google ADK**, **LiteLLM**, **Ollama**, and **ChromaDB**. The backend ingests user documents, extracts text, chunks and embeds content, retrieves relevant evidence, and generates grounded answers with citations for the React workspace.

## Capabilities

- **Document ingestion** for PDF, DOCX, and PPTX uploads.
- **Grounded RAG answers** with citation metadata returned to the frontend.
- **Google ADK agent runtime** for orchestration-compatible ingestion, retrieval, and answer-generation tools.
- **LiteLLM + Ollama integration** for local or Ollama-hosted chat models.
- **Persistent ChromaDB vector storage** with embedding-model scoped collections to avoid dimension mismatches.
- **Operational safeguards** including file validation, request timeouts, health checks, CORS, and structured error responses.

## System Architecture

```text
React Frontend
    |
    | HTTP/JSON + multipart uploads
    v
FastAPI Backend (app/main.py)
    |-- POST   /documents/upload
    |-- GET    /documents/list
    |-- DELETE /documents/{document_id}
    |-- POST   /chat/query
    |-- GET    /health
    |
    | ingestion
    v
extract_text -> chunk_text -> ollama_embed -> ChromaDB
    |
    | query
    v
classify_intents -> retrieve_chunks -> generate_answer -> citations
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI application, lifecycle hooks, and API endpoints. |
| `app/config.py` | Centralized settings loaded from environment variables and `.env`. |
| `app/schemas.py` | Pydantic request/response models. |
| `app/adk_runtime/` | Google ADK agents and orchestration-compatible tool wrappers. |
| `app/services/` | File persistence, document registry, and Ollama model capability checks. |
| `app/tools/` | Extraction, chunking, Ollama client, and Chroma vector-store functions. |
| `tests/` | Backend unit and integration tests. |
| `storage/` | Runtime uploads and Chroma persistence. Do not commit production data. |
| `frontend/` | React + TypeScript client application. |

## Prerequisites

- Python 3.12+
- Ollama reachable from the backend
- Required Ollama models pulled locally or available through your configured Ollama endpoint
- Node.js 20+ if you also run the frontend

Recommended local models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
ollama serve
```

## Configuration

Create a `.env` file in the repository root. The application also works with the defaults in `app/config.py`, but production deployments should set explicit values.

```env
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]

UPLOAD_DIR=storage/uploads
MAX_FILE_SIZE_MB=50

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_REQUEST_TIMEOUT=600
OLLAMA_EMBED_BATCH_SIZE=10

CHROMA_DIR=storage/chroma
CHROMA_COLLECTION_NAME=document_chunks
CHROMA_SCOPE_BY_EMBEDDING_MODEL=true
```

> For Ollama Cloud or another remote Ollama-compatible endpoint, set `OLLAMA_BASE_URL` and `OLLAMA_API_KEY` accordingly. Avoid printing or logging API keys.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Open the health endpoint:

```bash
curl http://localhost:8001/health
```

Expected response shape:

```json
{
  "status": "ok",
  "ollama_status": "ok",
  "timestamp": "2026-06-03T00:00:00+00:00"
}
```

## API Reference

### Upload a document

```bash
curl -X POST "http://localhost:8001/documents/upload" \
  -F "file=@sample.pdf" \
  -F "user_id=user_123"
```

### Ask a grounded question

```bash
curl -X POST "http://localhost:8001/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_123","message":"Summarize the renewal terms."}'
```

### List documents

```bash
curl "http://localhost:8001/documents/list?user_id=user_123"
```

### Delete a document

```bash
curl -X DELETE "http://localhost:8001/documents/<document_id>"
```

## Testing and Quality Gates

```bash
python -m pytest -q
```

If tests fail with missing packages such as `pydantic_settings`, install backend dependencies first:

```bash
pip install -r requirements.txt
```

## Troubleshooting

### Ollama is offline

- Confirm `ollama serve` is running.
- Check `OLLAMA_BASE_URL` and `OLLAMA_EMBED_URL`.
- Call `GET /health` and inspect `ollama_status`.

### Model does not support ADK tools

Google ADK tool/function calling requires a chat model that supports tool declarations. If `/chat/query` returns a capability error, switch to a tool-capable model such as `llama3.1` and restart the backend.

### Chroma embedding dimension mismatch

If uploads fail with a dimension mismatch, either keep a stable embedding model or configure a new collection name. The default `CHROMA_SCOPE_BY_EMBEDDING_MODEL=true` prevents most accidental cross-model collection reuse.

### Slow local answers

Local LLMs can be slow on CPU-only machines. Increase `OLLAMA_REQUEST_TIMEOUT`, use a smaller chat model, or reduce retrieved chunk counts in `app/config.py`.

## Production Readiness Checklist

- [ ] Replace the in-memory document registry with PostgreSQL or another durable database.
- [ ] Store original files in S3, GCS, Azure Blob Storage, or an equivalent object store.
- [ ] Add authentication, authorization, and tenant isolation.
- [ ] Add malware scanning and DLP controls for uploads.
- [ ] Add request tracing, metrics, and structured log export.
- [ ] Add RAG evaluation datasets and citation-quality regression tests.
- [ ] Back up ChromaDB or migrate to a managed vector database for large deployments.
