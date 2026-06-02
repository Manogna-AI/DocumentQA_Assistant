# Google ADK + Ollama — Document Q&A Assistant (v2)

A **production-oriented** document-grounded Q&A assistant using:

- **Google ADK 2.0** for multi-agent orchestration
- **Ollama** for local embeddings (`nomic-embed-text`) and chat (`llama3.1`)
- **FastAPI** backend with CORS, document management, error handling
- **ChromaDB** persistent vector store with cosine similarity
- Deterministic **PDF / DOCX / PPTX** extraction
- **Strict grounding** with citations and prompt-injection defence

---

## Architecture

```
Client (curl / UI)
    |
    v
FastAPI Backend (app/main.py)
    |
    +-- POST /documents/upload
    +-- POST /chat/query
    +-- GET  /documents/list
    +-- DELETE /documents/{id}
    +-- GET  /health
    |
    v
ADK Orchestrator (app/adk_runtime/orchestrator.py)
    |
    +-- Intent Classifier (QA / SUMMARY / DOC_CONTEXT / UPLOAD)
    |
    +-- Ingestion Agent --> extract_text -> chunk_text -> ollama_embed -> vector_store
    +-- Retrieval Agent --> ollama_embed -> vector_search
    +-- Answering Agent --> ollama_chat (grounded + citations)
    |
    +-- Ollama Server (localhost:11434)
    +-- ChromaDB (storage/chroma/)
```

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Ingestion Agent** | Accept uploads, extract text, chunk, embed, store | `extract_text`, `chunk_text`, `ollama_embed`, `vector_store.add` |
| **Retrieval Agent** | Embed query, top-K similarity search, filter | `ollama_embed`, `vector_store.search` |
| **Answering Agent** | Generate grounded answer with citations | `ollama_chat` |

## Key Improvements 

- Google ADK 2.0 integration — ADK-native agents in `app/adk_runtime/adk_agents.py`
- Modern Ollama API — uses `/api/embed` (batch) instead of legacy `/api/embeddings`
- Intent detection — classifies QA / SUMMARY / DOC_CONTEXT
- Multi-intent handling — processes multiple intents sequentially
- Ambiguity resolution — prompts user to select from multiple documents
- Error handling / rollback — failed ingestions marked as "failed"
- Retry logic — exponential backoff for Ollama requests
- Connection pooling — `requests.Session` for HTTP reuse
- CORS middleware — for frontend integration
- Document management — list, delete, status endpoints
- Cosine distance — explicit metric in ChromaDB
- Sentence-boundary chunking — smarter text splitting
- Centralised configuration — all settings in `config.py`

---

## Quick Start

### 1. Start Ollama

```bash
# Install from https://ollama.com
ollama pull nomic-embed-text
ollama pull llama3.1
ollama serve
```

### 2. Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env if needed
```

### 4. Run FastAPI server

```bash
uvicorn app.main:app --reload
```

### 5. Run with ADK Dev UI (optional)

```bash
adk web app/adk_runtime/
```

### 6. Upload a document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sample.pdf" \
  -F "user_id=user_123"
```

### 7. Ask a question

```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_123","message":"What does the document say about renewal?"}'
```

### 8. List documents

```bash
curl "http://localhost:8000/documents/list?user_id=user_123"
```

---

## Official Documentation References

- [Ollama API — /api/embed](https://docs.ollama.com/api/embed)
- [Ollama API — /api/chat](https://docs.ollama.com/api/chat)
- [Google ADK Python — PyPI](https://pypi.org/project/google-adk/)
- [Google ADK — Getting Started](https://adk.dev/get-started/python/)
- [Google ADK — SequentialAgent](https://adk.dev/agents/workflow-agents/sequential-agents/)
- [Google ADK — Multi-Agent Systems](https://adk.dev/2.0/)

---

## Production Checklist

- [ ] Authentication and RBAC
- [ ] Malware scanning for uploads
- [ ] Object storage (S3/GCS) for original files
- [ ] PostgreSQL for document metadata
- [ ] Qdrant / Milvus / Weaviate for scalable vector search
- [ ] Audit logs and observability
- [ ] RAG evaluation test set
- [ ] Citation validation layer
- [ ] Prompt-injection regression tests
- [ ] Frontend UI (left: docs, center: chat, right: citations)
