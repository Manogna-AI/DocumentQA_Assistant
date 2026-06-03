import { useCallback } from 'react';
import { sendQuery } from '@/services/chatService';
import { useAppStore } from '@/stores/appStore';
import { LOG_MESSAGE_PREVIEW_CHARS } from '@/config/frontend.config';
import type { Message } from '@/types/chat';

interface ErrorContext {
  code?: string;
  status?: number;
  message: string;
  isNetworkError: boolean;
  isTimeoutError: boolean;
  isServerError: boolean;
}

// ✓ Helper: Extract error details from axios error
function extractErrorContext(err: any): ErrorContext {
  const isNetworkError = err.code === 'ERR_NETWORK' || !err.response;
  const isTimeoutError = err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK_TIMEOUT';
  const status = err.response?.status;
  const isServerError = status && status >= 500;

  let message = 'Sorry, something went wrong. Please try again.';

  // ✓ Differentiate error messages based on error type
  if (isTimeoutError) {
    message = 'The request took too long. Please try a shorter question.';
  } else if (isNetworkError) {
    message = 'Cannot connect to the server. Please check your connection.';
  } else if (status === 503) {
    message = 'Service is temporarily unavailable. Please try again in a moment.';
  } else if (isServerError) {
    message = 'Server error. Please try again later.';
  } else if (err.response?.data?.detail) {
    message = err.response.data.detail;
  } else if (err.message) {
    message = err.message;
  }

  return {
    code: err.code,
    status,
    message,
    isNetworkError,
    isTimeoutError,
    isServerError,
  };
}

export function useChat() {
  const { userId, selectedDocumentId, addMessage, updateLastMessage, setCitations, setIsQuerying } =
    useAppStore();

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || useAppStore.getState().isQuerying) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };
      addMessage(userMsg);

      const loadingMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      };
      addMessage(loadingMsg);

      setIsQuerying(true);

      try {
        const response = await sendQuery({
          user_id: userId,
          message: text,
          document_id: selectedDocumentId || undefined,
        });

        const citations = response.citations ?? [];
        updateLastMessage(response.answer || 'No answer returned.', citations);
        setCitations(citations);

        console.debug('[useChat] Query successful', {
          messageLength: text.length,
          citationCount: citations.length,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        const errorCtx = extractErrorContext(err);

        // ✓ Log structured error information
        console.error('[useChat] Query failed', {
          errorCode: errorCtx.code,
          httpStatus: errorCtx.status,
          errorType: {
            isNetworkError: errorCtx.isNetworkError,
            isTimeoutError: errorCtx.isTimeoutError,
            isServerError: errorCtx.isServerError,
          },
          userMessage: text.substring(0, LOG_MESSAGE_PREVIEW_CHARS), // ✓ Use centralized config
          selectedDocumentId,
          timestamp: new Date().toISOString(),
        });

        // ✓ Show user-friendly error message
        setCitations([]);
        updateLastMessage(errorCtx.message, []);
      } finally {
        setIsQuerying(false);
      }
    },
    [userId, selectedDocumentId, addMessage, updateLastMessage, setCitations, setIsQuerying],
  );

  return { send };
}
