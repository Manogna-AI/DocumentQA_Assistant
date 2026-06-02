import axios from 'axios';
import { toast } from 'sonner';
import { API_TIMEOUT_MS, TOAST_TIMEOUT_DURATION_MS } from '@/config/frontend.config';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: API_TIMEOUT_MS,  // ✓ Use centralized config
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  console.debug(`[api] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.debug(`[api] ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    // ✓ Determine error type
    const isTimeout = error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK_TIMEOUT';
    const isNetworkError = error.code === 'ERR_NETWORK';
    const isConnectionRefused = error.code === 'ECONNREFUSED';
    const status = error.response?.status;
    
    // ✓ Extract error message
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred';
    
    console.error('[api] Request error:', {
      url: error.config?.url,
      code: error.code,
      status: error.response?.status,
      isTimeout,
      isNetworkError,
      isConnectionRefused,
      message,
    });

    // ✓ Show differentiated error messages
    if (isTimeout) {
      // Timeout: service is running but slow
      toast.error(
        'Request took too long. Please try a simpler question or check Ollama performance.',
        { duration: TOAST_TIMEOUT_DURATION_MS }
      );
    } else if (isConnectionRefused || isNetworkError) {
      // Connection refused: backend not running
      toast.error('Cannot connect to backend. Is the server running?');
    } else if (status === 503) {
      // Service unavailable: usually Ollama issue
      toast.error(
        'Service temporarily unavailable. Is Ollama running and responsive?',
        { duration: TOAST_TIMEOUT_DURATION_MS }
      );
    } else if (status === 500) {
      // Server error: backend crashed or threw
      toast.error('Server error. Please check backend logs.');
    } else if (status === 413) {
      // Payload too large: handled at source, but log if we see it
      console.warn('[api] Payload too large (413)');
    } else if (status === 415) {
      // Unsupported media type: handled at source
      console.warn('[api] Unsupported media type (415)');
    } else {
      // Generic error: show server message if available
      toast.error(message);
    }

    return Promise.reject(error);
  },
);

export default api;
