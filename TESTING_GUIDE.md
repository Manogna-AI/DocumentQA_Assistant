# Testing Guide — Backend & Frontend

## Quick Start

### Backend (Python/pytest)

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_backend.py -v

# Run specific test class
pytest tests/test_backend.py::TestClassifyIntents -v

# Run with detailed output
pytest tests/ -vv --tb=long
```

### Frontend (TypeScript/Vitest)

```bash
# Install dependencies
npm install

# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Run tests once (CI mode)
npm run test:run

# Generate coverage report
npm run test:coverage
```

---

## Test Structure

### Backend Test Organization

```
tests/
├── conftest.py              # Shared fixtures & configuration
├── test_backend.py          # Unit & integration tests
│
├── unit/
│   ├── test_orchestrator.py     # Intent classification tests
│   ├── test_answering_agent.py   # Answer generation tests
│   ├── test_retrieval_agent.py   # Document retrieval tests
│   ├── test_ingestion_agent.py   # Document upload tests
│   └── test_services.py          # Service layer tests
│
└── integration/
    ├── test_e2e_upload_query.py  # End-to-end workflows
    └── test_agent_chain.py       # Multi-agent orchestration
```

### Frontend Test Organization

```
frontend/src/__tests__/
├── setup.ts                    # Test environment setup
├── integration.test.ts         # Hooks, services, stores
│
├── unit/
│   ├── appStore.test.ts           # Zustand store tests
│   ├── useChat.test.ts            # Chat hook tests
│   ├── useDocuments.test.ts        # Document hook tests
│   └── api.test.ts                # API service tests
│
└── components/
    ├── ChatPanel.test.tsx      # Chat component tests
    ├── DocumentPanel.test.tsx   # Document component tests
    └── StatusBar.test.tsx       # Status bar tests
```

---

## What's Being Tested

### Backend Coverage

#### ✅ ORCHESTRATOR TESTS
- [x] Single intent classification (QA, upload, summary)
- [x] Multi-intent detection (compound questions)
- [x] Empty input handling
- [x] Regex injection resistance
- [ ] Performance on large inputs

#### ✅ ANSWERING AGENT TESTS
- [x] Answer generation with valid chunks
- [x] Handling of empty chunks (prevents hallucination)
- [x] Invalid JSON chunk parsing
- [x] Chunk limit enforcement (max 3)
- [x] Intent-specific system prompts (summary vs QA)
- [ ] Citation formatting validation

#### ✅ RETRIEVAL AGENT TESTS
- [x] Specific document retrieval
- [x] "Latest" document ID handling
- [x] Fallback to "default" user
- [x] Similarity threshold filtering
- [ ] Large result set pagination

#### ✅ INGESTION AGENT TESTS
- [x] Valid document ingestion
- [x] Empty document handling
- [x] Missing file error handling
- [x] Unsupported file type rejection
- [ ] Large file processing

#### ✅ DOCUMENT REGISTRY TESTS
- [x] Create, read, update, delete operations
- [x] List documents by user
- [x] Latest indexed document retrieval
- [x] Error handling for non-existent documents
- [ ] Concurrent access handling

#### ✅ VECTOR STORE TESTS
- [x] Store initialization
- [x] Add chunks operation
- [x] Search with filters
- [ ] Embedding dimension validation
- [ ] Update/delete chunk operations

---

### Frontend Coverage

#### ✅ STORE TESTS (appStore.ts)
- [x] Initialization with defaults
- [x] Message addition
- [x] Last message update
- [x] Theme toggle with localStorage persistence
- [x] Document selection
- [x] Clear all messages
- [ ] Undo/redo for messages

#### ✅ HOOK TESTS
- [x] useChat: Query sending, error handling
- [x] useChat: Message state updates
- [x] useDocumentList: Polling every 10s
- [x] useUploadDocument: Success/error handling
- [x] useDeleteDocument: Deletion workflow
- [ ] useChat: Retry logic with exponential backoff

#### ✅ SERVICE TESTS
- [x] Health check API calls
- [x] Document upload/list/delete operations
- [x] Chat query requests
- [x] Error logging and toast notifications
- [ ] Request timeout differentiation

#### ✅ INTEGRATION TESTS
- [x] Upload → List documents → Query flow
- [x] Multi-intent request handling
- [ ] Concurrent upload handling
- [ ] Recovery from network failures

---

## Current Test Coverage

### Backend Target: 85%+ Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| orchestrator.py | ~80% | ⚠️ Needs edge cases |
| answering_agent.py | ~75% | ⚠️ Missing citation tests |
| retrieval_agent.py | ~70% | ⚠️ Needs pagination tests |
| ingestion_agent.py | ~75% | ⚠️ Missing large file tests |
| document_registry.py | ~90% | ✅ Good |
| vector_store.py | ~65% | ⚠️ Needs validation tests |

### Frontend Target: 80%+ Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| appStore.ts | ~85% | ✅ Good |
| useChat.ts | ~70% | ⚠️ No retry logic |
| useDocuments.ts | ~80% | ✅ Good |
| services/ | ~75% | ⚠️ Error handling |
| API interceptors | ~60% | ⚠️ Needs timeout tests |

---

## Running Specific Test Scenarios

### Backend — Intent Classification

```bash
pytest tests/test_backend.py::TestClassifyIntents -v
```

Tests various user inputs:
- "What is the renewal date?" → QA intent
- "Upload this document" → Upload intent
- "Summarize for me" → Summary intent
- "Summarize AND explain payment terms" → Multi-intent

### Backend — Error Handling

```bash
pytest tests/test_backend.py -k "error" -v
```

Tests error scenarios:
- Empty chunk handling
- Invalid JSON parsing
- Missing files
- Unsupported file types

### Frontend — Chat Hook

```bash
npm run test -- useChat.test.ts
```

Tests:
- Message sending and state updates
- Error handling and user-friendly messages
- Loading states during requests
- Document ID inclusion in requests

### Frontend — Document Upload

```bash
npm run test -- useDocuments.test.ts
```

Tests:
- File upload success/failure
- Error message extraction
- Cache invalidation after upload
- Large file handling

---

## Debugging Tests

### Backend

```bash
# Run with full output and print statements
pytest tests/test_backend.py -vv --tb=long -s

# Run with pdb on failure
pytest tests/test_backend.py --pdb

# Run with logging
pytest tests/test_backend.py --log-cli-level=DEBUG
```

### Frontend

```bash
# Run tests in UI mode for visual inspection
npm run test:ui

# Run with additional console output
npm run test -- --reporter=verbose

# Run specific test and keep open
npm run test -- useChat.test.ts --watch
```

---

## Known Issues & Gaps

### 🔴 CRITICAL GAPS

**Backend:**
- [ ] No tests for regex DoS protection
- [ ] No concurrent upload handling tests
- [ ] No embedding dimension validation tests
- [ ] No tests for fallback logging (silent failures)

**Frontend:**
- [ ] No retry logic tests (feature not implemented)
- [ ] No Ollama status detection tests (bug in current code)
- [ ] No timeout differentiation tests
- [ ] No race condition tests for concurrent mutations

### 🟡 MEDIUM PRIORITY

**Backend:**
- [ ] Performance tests for large documents
- [ ] Load tests for concurrent queries
- [ ] Tests for structured error responses
- [ ] Request correlation ID tracing tests

**Frontend:**
- [ ] Component-level tests (ChatPanel, DocumentPanel)
- [ ] Accessibility tests (a11y)
- [ ] Snapshot tests for message formatting
- [ ] Browser compatibility tests

### 🟢 LOW PRIORITY

**Backend:**
- [ ] Tests for graceful degradation
- [ ] Tests for cache invalidation
- [ ] Tests for audit logging

**Frontend:**
- [ ] Performance tests for large message histories
- [ ] Memory leak detection
- [ ] Bundle size regression tests

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:run -- --coverage
      - uses: codecov/codecov-action@v3
```

---

## Best Practices

### ✅ DO

- Mock external dependencies (Ollama, ChromaDB)
- Test both success and error paths
- Use descriptive test names
- Keep tests isolated (no shared state)
- Use fixtures for common setup
- Test user-facing messages and UI updates
- Test async behavior with proper `await` and `waitFor`

### ❌ DON'T

- Hard-code timeouts (use `waitFor` with reasonable timeout)
- Mock entire modules when you can mock just the function
- Write tests that depend on test execution order
- Test implementation details instead of behavior
- Skip tests instead of fixing them
- Ignore flaky tests — fix the root cause

---

## Adding New Tests

### Backend Template

```python
def test_my_feature(mock_ollama_embed, sample_chunks):
    """Test description."""
    # Arrange
    expected_result = "something"
    
    # Act
    result = my_function(sample_chunks)
    
    # Assert
    assert result == expected_result
```

### Frontend Template

```typescript
it('does something when action happens', async () => {
  // Arrange
  const mockData = { ... };
  vi.mocked(apiService.call).mockResolvedValue(mockData);
  
  // Act
  const { result } = renderHook(() => useMyHook(), { wrapper });
  
  await act(async () => {
    result.current.doSomething();
  });
  
  // Assert
  await waitFor(() => {
    expect(result.current.state).toBe('expected');
  });
});
```

---

## Performance Benchmarks

Target query response times:

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Chat query (with retrieval) | < 3s | ~2-4s | ⚠️ Depends on Ollama |
| Document upload (5MB) | < 10s | ~8-15s | ⚠️ Acceptable |
| Health check | < 1s | ~0.5s | ✅ Good |
| Document list | < 1s | ~0.8s | ✅ Good |

---

## Troubleshooting

### Backend Tests Failing

**Issue:** `ModuleNotFoundError: No module named 'app'`
- **Fix:** Run from project root: `cd /path/to/google-docqa-assistant`

**Issue:** `ChromaDB connection error`
- **Fix:** Use mock fixtures instead: `@patch('app.tools.vector_store.vector_store')`

**Issue:** `Ollama timeout`
- **Fix:** Use mock Ollama: `@patch('app.tools.ollama_client.ollama_chat')`

### Frontend Tests Failing

**Issue:** `ReferenceError: localStorage is not defined`
- **Fix:** It's mocked in setup.ts; ensure setup file runs

**Issue:** `Cannot find module '@/...'`
- **Fix:** Check vitest.config.ts alias paths

**Issue:** `Timeout waiting for waitFor`
- **Fix:** Mock API calls or increase timeout
  ```ts
  await waitFor(() => expect(...).toBe(...), { timeout: 5000 });
  ```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Mock ADK Agents](./ARCHITECTURE_ANALYSIS.md#testing-adk-agents)

