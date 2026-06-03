/**
 * Frontend configuration for timeouts, polling intervals, and UI constants.
 * These values should match or be coordinated with backend settings in app/config.py
 */

export const FRONTEND_CONFIG = {
  // ── HTTP Timeouts (milliseconds) ──────────────────────────────────
  /** API request timeout (10 minutes for slower local Ollama LLM responses) */
  API_TIMEOUT_MS: 600_000,

  /** Upload request timeout (5 minutes for large files) */
  UPLOAD_TIMEOUT_MS: 300_000,

  /** Health check timeout (5 seconds for quick checks) */
  HEALTH_CHECK_TIMEOUT_MS: 5_000,

  // ── Polling & Intervals (milliseconds) ────────────────────────────
  /** Document list polling interval for status updates */
  DOCUMENT_POLL_INTERVAL_MS: 10_000,

  // ── Toast/UI Duration (milliseconds) ───────────────────────────────
  /** Duration for timeout/slow operation toast messages */
  TOAST_TIMEOUT_DURATION_MS: 5_000,

  // ── Logging & Preview (characters) ────────────────────────────────
  /** Max characters to show in logs for message previews */
  LOG_MESSAGE_PREVIEW_CHARS: 50,

  // ── Input Limits ──────────────────────────────────────────────────
  /** Max user message length (5KB) */
  MAX_USER_MESSAGE_LENGTH: 5_000,
};

// Export individual values for convenience
export const {
  API_TIMEOUT_MS,
  UPLOAD_TIMEOUT_MS,
  HEALTH_CHECK_TIMEOUT_MS,
  DOCUMENT_POLL_INTERVAL_MS,
  TOAST_TIMEOUT_DURATION_MS,
  LOG_MESSAGE_PREVIEW_CHARS,
  MAX_USER_MESSAGE_LENGTH,
} = FRONTEND_CONFIG;
