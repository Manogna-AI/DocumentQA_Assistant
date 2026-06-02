import api from './api';
import { HEALTH_CHECK_TIMEOUT_MS } from '@/config/frontend.config';

export interface HealthStatus {
  api: boolean;
  ollama: boolean;
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const { data } = await api.get('/health', { timeout: HEALTH_CHECK_TIMEOUT_MS });  // ✓ Use centralized config
    
    // ✓ Parse API status
    const apiOk = data.status === 'ok';
    
    // ✓ Parse Ollama status from response
    // Backend returns ollama_status: "ok" | "down"
    const ollamaOk = data.ollama_status === 'ok';
    
    // ✓ Log for debugging
    if (!ollamaOk) {
      console.warn('[healthService] Ollama is down or unreachable', {
        ollama_status: data.ollama_status,
        timestamp: data.timestamp,
      });
    }
    
    return { api: apiOk, ollama: ollamaOk };
  } catch (err) {
    console.warn('[healthService] Health check failed:', err);
    return { api: false, ollama: false };
  }
}
