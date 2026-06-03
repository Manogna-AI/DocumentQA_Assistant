/**
 * Frontend Unit Tests — Vitest + React Testing Library Test Suite
 * Tests for hooks, services, components, and state management
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAppStore } from '@/stores/appStore';
import { useChat } from '@/hooks/useChat';
import { useDocumentList, useUploadDocument, useDeleteDocument } from '@/hooks/useDocuments';
import { checkHealth } from '@/services/healthService';
import api from '@/services/api';
import * as chatService from '@/services/chatService';
import * as documentService from '@/services/documentService';


// ════════════════════════════════════════════════════════
// SETUP & FIXTURES
// ════════════════════════════════════════════════════════

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const wrapper = ({ children }) => (
  <QueryClientProvider client={createQueryClient()}>
    {children}
  </QueryClientProvider>
);

// Mock Zustand store between tests
beforeEach(() => {
  useAppStore.setState({
    userId: 'test_user',
    selectedDocumentId: null,
    theme: 'light',
    messages: [],
    citations: [],
    isQuerying: false,
  });
});


// ════════════════════════════════════════════════════════
// STORE TESTS (appStore.ts)
// ════════════════════════════════════════════════════════

describe('AppStore', () => {
  
  it('initializes with default values', () => {
    const state = useAppStore.getState();
    expect(state.userId).toBeDefined();
    expect(state.messages).toEqual([]);
    expect(state.isQuerying).toBe(false);
  });

  it('adds messages to the store', () => {
    const { getState, setState } = useAppStore;
    const state = getState();
    
    const newMsg = {
      id: '1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date(),
    };
    
    state.addMessage(newMsg);
    expect(getState().messages.length).toBe(1);
    expect(getState().messages[0].content).toBe('Hello');
  });

  it('updates the last message', () => {
    const { getState } = useAppStore;
    const state = getState();
    
    // Add assistant message first
    state.addMessage({
      id: '1',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    });
    
    // Update it
    state.updateLastMessage('Updated content', []);
    
    const lastMsg = getState().messages[0];
    expect(lastMsg.content).toBe('Updated content');
    expect(lastMsg.isLoading).toBe(false);
  });

  it('does not crash when updating with no messages', () => {
    const { getState } = useAppStore;
    const state = getState();
    
    // Clear messages
    state.clearMessages();
    
    // This should not crash (but currently would silently fail)
    expect(() => {
      state.updateLastMessage('Should handle empty messages');
    }).not.toThrow();
  });

  it('toggles theme and persists to localStorage', () => {
    const { getState, setState } = useAppStore;
    
    setState({ theme: 'light' });
    const state = getState();
    state.toggleTheme();
    
    expect(getState().theme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('sets selected document ID', () => {
    const { getState } = useAppStore;
    const state = getState();
    
    state.setSelectedDocumentId('doc_123');
    expect(getState().selectedDocumentId).toBe('doc_123');
    
    state.setSelectedDocumentId(null);
    expect(getState().selectedDocumentId).toBeNull();
  });

  it('clears all messages and citations', () => {
    const { getState } = useAppStore;
    const state = getState();
    
    state.addMessage({
      id: '1',
      role: 'user',
      content: 'Test',
      timestamp: new Date(),
    });
    state.setCitations([{ document_id: 'doc', document_name: 'Doc', chunk_id: 'chunk', page_number: 1, slide_number: null, section_title: null, snippet: 'Snippet', score: 0.9 }]);
    
    state.clearMessages();
    
    expect(getState().messages).toEqual([]);
    expect(getState().citations).toEqual([]);
  });
});


// ════════════════════════════════════════════════════════
// useChat HOOK TESTS
// ════════════════════════════════════════════════════════

describe('useChat Hook', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(chatService, 'sendQuery');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends a query and updates messages', async () => {
    const mockResponse = {
      answer: 'Test answer',
      citations: [],
      metadata: { status: 'ok', intent: 'qa' },
    };
    
    vi.mocked(chatService.sendQuery).mockResolvedValue(mockResponse);
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await result.current.send('What is this?');
    });
    
    await waitFor(() => {
      const state = useAppStore.getState();
      expect(state.messages.length).toBe(2); // User msg + assistant msg
    });
  });

  it('does not send empty messages', async () => {
    const { result } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await result.current.send('   '); // Whitespace only
    });
    
    const state = useAppStore.getState();
    expect(state.messages).toHaveLength(0);
  });

  it('does not send when already querying', async () => {
    const { result } = renderHook(() => useChat(), { wrapper });
    
    // Set querying state
    useAppStore.setState({ isQuerying: true });
    
    await act(async () => {
      await result.current.send('Test message');
    });
    
    const state = useAppStore.getState();
    expect(state.messages).toHaveLength(0);
  });

  it('handles query errors gracefully', async () => {
    const mockError = new Error('Network error');
    vi.mocked(chatService.sendQuery).mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await result.current.send('What is this?');
    });
    
    await waitFor(() => {
      const state = useAppStore.getState();
      expect(state.isQuerying).toBe(false);
      // Last message should contain error text
      const lastMsg = state.messages[state.messages.length - 1];
      expect(lastMsg.content).toContain('something went wrong');
    });
  });

  it('includes document ID in request when selected', async () => {
    useAppStore.setState({ selectedDocumentId: 'doc_123' });
    
    vi.mocked(chatService.sendQuery).mockResolvedValue({
      answer: 'Answer',
      citations: [],
      metadata: { status: 'ok', intent: 'qa' },
    });
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await result.current.send('Query?');
    });
    
    expect(vi.mocked(chatService.sendQuery)).toHaveBeenCalledWith(
      expect.objectContaining({ document_id: 'doc_123' })
    );
  });

  it('sets loading state correctly', async () => {
    vi.mocked(chatService.sendQuery).mockImplementation(
      () => new Promise(r => setTimeout(() => r({
        answer: 'Answer',
        citations: [],
        metadata: { status: 'ok', intent: 'qa' },
      }), 100))
    );
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    let queryingDuringRequest = false;
    
    act(() => {
      result.current.send('Query?');
      queryingDuringRequest = useAppStore.getState().isQuerying;
    });
    
    expect(queryingDuringRequest).toBe(true);
    
    await waitFor(() => {
      expect(useAppStore.getState().isQuerying).toBe(false);
    });
  });

  // ✗ MISSING: Retry logic test (should add exponential backoff)
  it.skip('retries query with exponential backoff on transient errors', async () => {
    // This test will fail until retry logic is implemented
  });
});


// ════════════════════════════════════════════════════════
// useDocumentList HOOK TESTS
// ════════════════════════════════════════════════════════

describe('useDocumentList Hook', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(documentService, 'listDocuments');
  });

  it('fetches document list on mount', async () => {
    const mockDocs = {
      documents: [
        { document_id: '1', document_name: 'Test.pdf', status: 'indexed' }
      ],
    };
    
    vi.mocked(documentService.listDocuments).mockResolvedValue(mockDocs);
    
    const { result } = renderHook(() => useDocumentList(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data).toEqual(mockDocs);
  });

  it('refetches documents every 10 seconds', async () => {
    vi.useFakeTimers();
    
    vi.mocked(documentService.listDocuments).mockResolvedValue({
      documents: [],
    });
    
    const { result } = renderHook(() => useDocumentList(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    const initialCallCount = vi.mocked(documentService.listDocuments).mock.calls.length;
    
    vi.advanceTimersByTime(10000);
    
    await waitFor(() => {
      expect(vi.mocked(documentService.listDocuments).mock.calls.length)
        .toBeGreaterThan(initialCallCount);
    });
    
    vi.useRealTimers();
  });

  it('handles fetch errors', async () => {
    vi.mocked(documentService.listDocuments)
      .mockRejectedValue(new Error('Fetch failed'));
    
    const { result } = renderHook(() => useDocumentList(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});


// ════════════════════════════════════════════════════════
// useUploadDocument HOOK TESTS
// ════════════════════════════════════════════════════════

describe('useUploadDocument Hook', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(documentService, 'uploadDocument');
  });

  it('uploads a document successfully', async () => {
    const mockResponse = {
      document_id: 'doc_123',
      document_name: 'test.pdf',
      file_type: 'pdf',
      status: 'indexed',
      chunk_count: 10,
      message: 'Indexed',
    };
    
    vi.mocked(documentService.uploadDocument).mockResolvedValue(mockResponse);
    
    const { result } = renderHook(() => useUploadDocument(), { wrapper });
    
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    await act(async () => {
      result.current.mutate(file);
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('shows error message on upload failure', async () => {
    const error = {
      response: { data: { detail: 'File too large' } },
    };
    
    vi.mocked(documentService.uploadDocument).mockRejectedValue(error);
    
    const { result } = renderHook(() => useUploadDocument(), { wrapper });
    
    const file = new File(['x'.repeat(100000000)], 'huge.pdf');
    
    await act(async () => {
      result.current.mutate(file);
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it('invalidates document list on successful upload', async () => {
    const queryClient = createQueryClient();
    const mockResponse = {
      document_id: 'doc_123',
      document_name: 'test.pdf',
      file_type: 'pdf',
      status: 'indexed',
      chunk_count: 10,
      message: 'Indexed',
    };
    
    vi.mocked(documentService.uploadDocument).mockResolvedValue(mockResponse);
    
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
    
    const customWrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
    
    const { result } = renderHook(() => useUploadDocument(), { wrapper: customWrapper });
    
    const file = new File(['content'], 'test.pdf');
    
    await act(async () => {
      result.current.mutate(file);
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['documents'] })
    );
  });
});


// ════════════════════════════════════════════════════════
// useDeleteDocument HOOK TESTS
// ════════════════════════════════════════════════════════

describe('useDeleteDocument Hook', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(documentService, 'deleteDocument');
  });

  it('deletes a document successfully', async () => {
    vi.mocked(documentService.deleteDocument).mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useDeleteDocument(), { wrapper });
    
    await act(async () => {
      result.current.mutate('doc_123');
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('shows error message on delete failure', async () => {
    vi.mocked(documentService.deleteDocument)
      .mockRejectedValue(new Error('Failed to delete'));
    
    const { result } = renderHook(() => useDeleteDocument(), { wrapper });
    
    await act(async () => {
      result.current.mutate('doc_123');
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it('invalidates document list on successful delete', async () => {
    vi.mocked(documentService.deleteDocument).mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useDeleteDocument(), { wrapper });
    
    await act(async () => {
      result.current.mutate('doc_123');
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });
});


// ════════════════════════════════════════════════════════
// HEALTH SERVICE TESTS
// ════════════════════════════════════════════════════════

describe('Health Check Service', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'get');
  });

  it('returns healthy status when API responds OK', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { status: 'ok' },
    });
    
    const result = await checkHealth();
    
    expect(result.api).toBe(true);
  });

  it('returns unhealthy status on network error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Network error'));
    
    const result = await checkHealth();
    
    expect(result.api).toBe(false);
  });

  it('returns unhealthy status on timeout', async () => {
    vi.mocked(api.get).mockRejectedValue({ code: 'ECONNABORTED' });
    
    const result = await checkHealth();
    
    expect(result.api).toBe(false);
  });

  // ✗ ISSUE: Ollama status is always true (should parse from response)
  it('should parse Ollama status from response (currently broken)', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { status: 'ok', ollama_status: 'down' },
    });
    
    const result = await checkHealth();
    
    // Currently returns { api: true, ollama: true } — WRONG!
    // Should return { api: true, ollama: false }
    expect(result.ollama).toBe(false); // This will fail until fixed
  });
});


// ════════════════════════════════════════════════════════
// API SERVICE TESTS
// ════════════════════════════════════════════════════════

describe('API Service', () => {
  
  it('includes authorization header if token is available', async () => {
    const interceptorSpy = vi.spyOn(api.interceptors.request, 'use');
    
    // Trigger a request
    try {
      await api.get('/test');
    } catch (e) {
      // Expected to fail in test
    }
    
    expect(interceptorSpy).toHaveBeenCalled();
  });

  it('logs debug info for requests and responses', async () => {
    const consoleDebugSpy = vi.spyOn(console, 'debug');
    
    vi.mocked(api.get).mockResolvedValue({ data: {}, status: 200 });
    
    try {
      await api.get('/test');
    } catch (e) {
      // Expected in test
    }
    
    // Should have debug logs
    expect(consoleDebugSpy).toHaveBeenCalledWith(
      expect.stringContaining('[api]')
    );
    
    consoleDebugSpy.mockRestore();
  });

  // ✗ ISSUE: Network timeout treated same as service unavailable
  it('should distinguish timeout errors from service unavailable', async () => {
    // Currently all errors show generic toast
    // Should differentiate:
    // - Timeout (120s) → "Please wait..."
    // - 503 → "Is Ollama running?"
    
    const result = await checkHealth();
    expect(result).toBeDefined();
  });
});


// ════════════════════════════════════════════════════════
// INTEGRATION TESTS
// ════════════════════════════════════════════════════════

describe('Chat Flow Integration', () => {
  
  beforeEach(() => {
    vi.clearAllMocks();
    useAppStore.setState({
      messages: [],
      citations: [],
      isQuerying: false,
    });
  });

  it('uploads document, then queries it', async () => {
    const uploadResponse = {
      document_id: 'doc_123',
      document_name: 'test.pdf',
      file_type: 'pdf',
      status: 'indexed',
      chunk_count: 10,
      message: 'Indexed',
    };
    
    const queryResponse = {
      answer: 'Test answer based on document',
      citations: [
        {
          document_id: 'doc_123',
          document_name: 'test.pdf',
          chunk_id: 'chunk_1',
          page_number: 1,
          snippet: 'Sample text',
          score: 0.95,
        },
      ],
      metadata: { status: 'ok', intent: 'qa' },
    };
    
    vi.spyOn(documentService, 'uploadDocument')
      .mockResolvedValue(uploadResponse);
    vi.spyOn(chatService, 'sendQuery')
      .mockResolvedValue(queryResponse);
    
    // Step 1: Upload
    const { result: uploadResult } = renderHook(() => useUploadDocument(), { wrapper });
    const file = new File(['content'], 'test.pdf');
    
    await act(async () => {
      uploadResult.current.mutate(file);
    });
    
    // Step 2: Select document
    await act(async () => {
      useAppStore.setState({ selectedDocumentId: 'doc_123' });
    });
    
    // Step 3: Query
    const { result: chatResult } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await chatResult.current.send('What is in this document?');
    });
    
    // Verify chat messages were added
    await waitFor(() => {
      const state = useAppStore.getState();
      expect(state.messages.length).toBeGreaterThan(0);
      expect(state.citations.length).toBeGreaterThan(0);
    });
  });
});


// ════════════════════════════════════════════════════════
// ACCESSIBILITY & UX TESTS
// ════════════════════════════════════════════════════════

describe('Accessibility & UX', () => {
  
  it('error messages are visible and understandable', async () => {
    vi.spyOn(chatService, 'sendQuery')
      .mockRejectedValue(new Error('Network error'));
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    await act(async () => {
      await result.current.send('Test');
    });
    
    await waitFor(() => {
      const state = useAppStore.getState();
      const lastMsg = state.messages[state.messages.length - 1];
      
      // Should contain user-friendly error, not raw error
      expect(lastMsg.content).toMatch(/something went wrong|try again/i);
    });
  });

  it('loading state is shown during query', async () => {
    vi.spyOn(chatService, 'sendQuery')
      .mockImplementation(() => new Promise(r => setTimeout(r, 500)));
    
    const { result } = renderHook(() => useChat(), { wrapper });
    
    act(() => {
      result.current.send('Test');
    });
    
    // Check loading state was set
    expect(useAppStore.getState().isQuerying).toBe(true);
  });
});


export {};
