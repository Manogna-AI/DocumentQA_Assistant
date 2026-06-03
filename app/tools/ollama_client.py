"""
Ollama API client — embeddings and chat.

CRITICAL CHANGES from v1:
  * Embeddings: migrated from legacy /api/embeddings (single, "prompt")
    to the modern /api/embed (batch, "input") per official Ollama docs.
    Ref: https://docs.ollama.com/api/embed
  * Added requests.Session for HTTP connection pooling.
  * Added retry logic with exponential back-off (configurable).
"""

import time
import logging
import requests

from app.config import settings

logger = logging.getLogger(__name__)

# ── Shared session for connection pooling ────────────────────
_session = requests.Session()


def _retry_request(method: str, url: str, **kwargs) -> requests.Response:
    """Execute an HTTP request with exponential back-off retry."""
    max_retries = settings.ollama_max_retries
    timeout = settings.ollama_request_timeout

    for attempt in range(1, max_retries + 1):
        try:
            resp = _session.request(
                method, url, timeout=timeout, **kwargs
            )
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == max_retries:
                logger.error(
                    "Ollama request failed after %d attempts: %s",
                    max_retries, exc,
                )
                raise
            wait = 2 ** attempt
            logger.warning(
                "Ollama request attempt %d/%d failed (%s). Retrying in %ds...",
                attempt, max_retries, exc, wait,
            )
            time.sleep(wait)
        except requests.HTTPError:
            raise  # Don't retry on 4xx/5xx
    # Should not reach here, but satisfy type checker
    raise RuntimeError("Unexpected retry loop exit")


# ── Embeddings (modern /api/embed endpoint) ──────────────────
def ollama_embed(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using the modern Ollama /api/embed endpoint.

    Official API (https://docs.ollama.com/api/embed):
      POST /api/embed
      Body: {"model": "...", "input": ["text1", "text2", ...]}
      Response: {"embeddings": [[...], [...], ...]}
    """
    resp = _retry_request(
        "POST",
        f"{settings.ollama_embed_url}/api/embed",
        json={
            "model": settings.ollama_embedding_model,
            "input": texts,
        },
    )
    data = resp.json()
    embeddings = data.get("embeddings", [])

    if len(embeddings) != len(texts):
        raise ValueError(
            f"Ollama returned {len(embeddings)} embeddings "
            f"for {len(texts)} inputs"
        )
    return embeddings


# ── Chat (/api/chat endpoint) ────────────────────────────────
def ollama_chat(messages: list[dict], stream: bool = False) -> str:
    """
    Generate a chat response using Ollama /api/chat.

    Official API (https://docs.ollama.com/api/chat):
      POST /api/chat
      Body: {"model": "...", "messages": [...], "stream": false}
      Response: {"message": {"content": "..."}}
    """
    resp = _retry_request(
        "POST",
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": settings.ollama_chat_model,
            "messages": messages,
            "stream": stream,
        },
    )
    return resp.json()["message"]["content"]
