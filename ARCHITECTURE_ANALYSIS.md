# Google DocQA Assistant — Architecture Analysis & Improvement Guide

## Executive Summary
The DocQA Assistant is a multi-agent agentic AI application with a React frontend and FastAPI backend using Google ADK. While the architecture is solid, there are critical issues around error handling, state management, validation, and test coverage that need immediate attention.

---

## 🔴 CRITICAL ISSUES BY COMPONENT

### FRONTEND ISSUES

#### 1. **App Store (appStore.ts) — Race Conditions & Missing Validation**
**Severity:** CRITICAL
- **Issue:** `updateLastMessage()` mutates array without checking if message exists
- **Impact:** Silent failures when message array is empty; UI doesn't update
- **Current Code:**
  ```ts
  updateLastMessage: (content, citations) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs[msgs.length - 1];
    if (last && last.role === 'assistant') { // ✗ No error if no messages
      msgs[msgs.length - 1] = { ...last, content, citations, isLoading: false };
    }
    return { messages: msgs };
  })
  ```
- **Fix:** Add validation and logging for edge cases

#### 2. **useChat Hook — No Retry Logic for Failed Queries**
**Severity:** HIGH
- **Issue:** Failed queries are silently retried 0 times; user gets immediate error
- **Impact:** Network blips result in bad UX; no exponential backoff
- **Fix:** Implement retry mechanism with exponential backoff

#### 3. **useDocuments Hook — Missing Error Details**
**Severity:** MEDIUM
- **Issue:** `onError` in delete mutation doesn't extract error message
  ```ts
  onError: () => toast.error('Failed to delete document'), // ✗ No details
  ```
- **Impact:** Users don't know WHY delete failed
- **Fix:** Extract and show `err?.response?.data?.detail`

#### 4. **Health Check Service — Incorrect Ollama Status Detection**
**Severity:** MEDIUM
- **Issue:** Returns `ollama: true` even if health endpoint says Ollama is down
  ```ts
  const { data } = await api.get('/health', ...);
  return { api: data.status === 'ok', ollama: true }; // ✗ Always true!
  ```
- **Impact:** StatusBar shows green even when Ollama is unavailable
- **Fix:** Parse `data.ollama_status` from backend

#### 5. **API Service — No Request Timeout Differentiation**
**Severity:** MEDIUM
- **Issue:** Treats 120s timeout error same as 503 (Ollama down)
- **Impact:** Legitimate slow responses trigger "Is Ollama running?" message
- **Fix:** Distinguish timeout errors (show "Please wait") vs unavailable (show "Is Ollama running?")

#### 6. **useDocumentList — No Loading State During Polling**
**Severity:** LOW
- **Issue:** 10s polling doesn't show user that status is being checked
- **Impact:** Ambiguous UX during document indexing
- **Fix:** Add `isRefetching` state display

#### 7. **TypeScript Strictness — Missing Type Definitions**
**Severity:** MEDIUM
- **Issue:** Using `any` in error handling
  ```ts
  onError: (err: any) => // ✗ Loses type safety
  ```
- **Impact:** IDE can't help with error shape; runtime errors likely
- **Fix:** Define `ApiError` type with discriminated union

#### 8. **Message Timestamps — Client-Side Only**
**Severity:** LOW
- **Issue:** Timestamps are created locally; can be inconsistent
- **Impact:** Race conditions if user's clock is wrong
- **Fix:** Use server timestamps for messages

---

### BACKEND ISSUES

#### 1. **Orchestrator Agent — Regex Complexity Without Validation**
**Severity:** HIGH
- **Issue:** `classify_intents()` uses regex without escaped user input
  ```python
  if re.search(qa_pattern, text) or has_question_mark or not intents:
      # ✗ `text` is not escaped; regex DoS possible
  ```
- **Impact:** Malicious input could cause regex catastrophic backtracking
- **Fix:** Pre-compile regex patterns and escape input

#### 2. **Answering Agent — Hardcoded Limits & No Validation**
**Severity:** MEDIUM
- **Issue:** Chunks limited to 3 without configurable limit; context trimmed to 800 chars
  ```python
  used_chunks = chunk_list[:3]  # ✗ Hardcoded
  text = chunk.get("text", "")[:800]  # ✗ Hardcoded
  ```
- **Impact:** Can't adjust for different model capabilities
- **Fix:** Move to `config.py` with validation

#### 3. **Ingestion Agent — No File Size Validation at Tool Level**
**Severity:** HIGH
- **Issue:** FastAPI validates `max_file_size_mb`, but ADK tool doesn't
  ```python
  def ingest_document(file_path: str, ...) -> dict:
      # ✗ No check if file actually exists or is readable
  ```
- **Impact:** Tool crashes if file is corrupted or disappears
- **Fix:** Add file existence/readability checks

#### 4. **Retrieval Agent — Fallback Logic Too Broad**
**Severity:** MEDIUM
- **Issue:** Falls back to `user_id="default"` silently; users don't know why
  ```python
  if not results and user_id != "default":
      results = _search_all_documents(..., "default")  # ✗ Silent fallback
  ```
- **Impact:** User queries documents they uploaded, but get results from "default" user
- **Fix:** Log fallback and include in response metadata

#### 5. **Vector Store — No Embedding Dimension Validation**
**Severity:** MEDIUM
- **Issue:** Embeddings added without checking dimension matches
  ```python
  self.collection.add(
      ids=ids,
      embeddings=embeddings,  # ✗ What if embedding is 768-dim but collection is 384?
      metadatas=metas,
  )
  ```
- **Impact:** ChromaDB raises cryptic error on dimension mismatch
- **Fix:** Validate embedding dimensions on first add

#### 6. **Document Registry — In-Memory Only (Production Risk)**
**Severity:** CRITICAL
- **Issue:** All document metadata is lost on server restart
- **Impact:** Users can't list documents after restart; vector store is orphaned
- **Fix:** Replace with SQLite/PostgreSQL as noted in TODO comment

#### 7. **Config — Magic Numbers Scattered**
**Severity:** MEDIUM
- **Issue:** Chunk limits (3), text trim (800), similarity threshold (0.25) are hardcoded in tools
- **Impact:** Can't experiment with different settings without code changes
- **Fix:** Move ALL tunable parameters to `config.py`

#### 8. **Error Handling — No Structured Error Responses**
**Severity:** HIGH
- **Issue:** Tools return `{"status": "not_found"}` but FastAPI might return 500 on crash
- **Impact:** Frontend can't distinguish "no results" from "server error"
- **Fix:** Define error codes (ERR_NO_RESULTS, ERR_INVALID_INPUT, etc.)

#### 9. **Logging — Inconsistent Levels & No Request ID**
**Severity:** MEDIUM
- **Issue:** Some functions log at INFO, others at WARNING; no request correlation
- **Impact:** Hard to trace a single user request through logs
- **Fix:** Add request ID middleware and use structlog

#### 10. **ADK Model Selection — Hardcoded in Every Agent**
**Severity:** MEDIUM
- **Issue:** Every agent defines `MODEL = f"ollama_chat/{settings.ollama_chat_model}"`
- **Impact:** Model choice is duplicated 3x; can't switch models per agent
- **Fix:** Centralize model selection in orchestrator

---

### INTEGRATION ISSUES

#### 1. **Frontend ↔ Backend Contract Not Validated**
**Severity:** HIGH
- **Issue:** Frontend expects `response.citations` but backend might return null/undefined
- **Impact:** Runtime crashes in ChatPanel on successful query
- **Fix:** Use OpenAPI/Swagger validation; add API tests

#### 2. **Concurrent Document Uploads — No Conflict Handling**
**Severity:** MEDIUM
- **Issue:** If user uploads 2 files simultaneously, `document_id` might collide
- **Impact:** Second upload overwrites first in vector store
- **Fix:** Use UUID for document_id; validate on backend

#### 3. **Health Check Race Condition**
**Severity:** MEDIUM
- **Issue:** Frontend polls `/health` every 15s; backend doesn't check if Ollama is ACTUALLY healthy during requests
- **Impact:** User sees green status, but chat request fails anyway
- **Fix:** Check Ollama health at start of each agent execution

#### 4. **Missing Request Timeout Coordination**
**Severity:** MEDIUM
- **Issue:** Frontend timeout is 120s, backend timeout is 180s
- **Impact:** Frontend gives up before backend finishes, user thinks request failed
- **Fix:** Frontend timeout should be 90s max (shorter than backend)

---

## ✅ IMPROVEMENTS ROADMAP

### Phase 1: Validation & Error Handling (Week 1)
- [ ] Add input validation to all tools
- [ ] Define structured error responses
- [ ] Add request ID middleware for tracing
- [ ] Create error type discriminated union (frontend)

### Phase 2: State Management & UX (Week 2)
- [ ] Fix race conditions in useChat
- [ ] Add retry logic with exponential backoff
- [ ] Implement request timeout differentiation
- [ ] Show meaningful error messages

### Phase 3: Configuration & Flexibility (Week 3)
- [ ] Move all magic numbers to config
- [ ] Centralize model selection
- [ ] Add per-agent model override capability
- [ ] Environment-specific configs

### Phase 4: Production Hardening (Week 4)
- [ ] Replace in-memory registry with SQLite
- [ ] Add structured logging (structlog)
- [ ] Implement request correlation IDs
- [ ] Add API contract tests

### Phase 5: Testing & Coverage (Ongoing)
- [ ] Unit tests for all tools (85%+ coverage)
- [ ] Integration tests for agent flows
- [ ] E2E tests for common workflows
- [ ] Load testing on embedding/retrieval

---

## 📋 SEVERITY SCALE

| Level | Impact | Action |
|-------|--------|--------|
| CRITICAL | Production outage / data loss | Fix immediately |
| HIGH | Significant UX/reliability issue | Fix within 1-2 days |
| MEDIUM | Maintainability / scalability issue | Fix within 1 week |
| LOW | Polish / nice-to-have | Fix when time permits |

