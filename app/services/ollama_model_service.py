"""Ollama model capability checks for the Google ADK agent runtime.

The DocQA chat flow uses Google ADK agents with Python tools. ADK sends those
functions to the configured LLM as Ollama chat ``tools``. Therefore the selected
Ollama chat model must advertise native tool/function-calling support.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests

from app.config import settings


RECOMMENDED_TOOL_MODELS = ("llama3.1", "qwen3")


def is_ollama_tool_support_error(exc: BaseException) -> bool:
    """Return True when a runtime exception is Ollama's tool-support failure.

    This is a safety net for cases where a model/proxy does not expose reliable
    `/api/show` capabilities but still rejects the ADK `tools` payload at
    `/api/chat`. Handling this before the generic ADK exception path prevents
    the long LiteLLM/ADK stack trace from becoming a 500 response.
    """
    current: BaseException | None = exc
    while current is not None:
        message = str(current).lower()
        if "does not support tools" in message or "doesn't support tools" in message:
            return True
        current = current.__cause__ or current.__context__
    return False


class OllamaModelCapabilityError(RuntimeError):
    """Raised when the configured Ollama chat model cannot run ADK tools."""


#def _show_model(model: str) -> dict[str, Any]:
#    """Return Ollama `/api/show` metadata for a model."""
#    resp = requests.post(
#        f"{settings.ollama_base_url}/api/show",
#        json={"model": model},
#        timeout=settings.ollama_health_check_timeout,
#    )
#    resp.raise_for_status()
#    return resp.json()


def _show_model(model: str) -> dict[str, Any]:
    """Return Ollama `/api/show` metadata for a model."""
    # Cloud models don't have local metadata
    if model.endswith("-cloud"):
        return {"template": "tools supported"}
    
    headers = {}
    if settings.ollama_api_key:
        headers["Authorization"] = f"Bearer {settings.ollama_api_key}"

    resp = requests.post(
        f"{settings.ollama_base_url}/api/show",
        json={"name": model},
        headers=headers,
        timeout=settings.ollama_health_check_timeout,
    )
    resp.raise_for_status()
    return resp.json()


def _probe_chat_tool_support(model: str) -> bool:
    """Probe `/api/chat` directly when `/api/show` has no capabilities field."""
    resp = requests.post(
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Return OK."}],
            "stream": False,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "docqa_tool_probe",
                        "description": "No-op probe for native tool support.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            ],
        },
        timeout=settings.ollama_health_check_timeout,
    )
    if resp.status_code == 400 and "support tools" in resp.text.lower():
        return False
    resp.raise_for_status()
    return True


@lru_cache(maxsize=16)
def ollama_model_supports_tools(model: str) -> bool:
    """Return whether an Ollama model advertises the `tools` capability.

    Ollama exposes native model capabilities via `/api/show`. Models without
    `tools` will reject ADK requests that include function declarations with the
    exact error seen for `orca-mini:3b`: "does not support tools".
    """
    metadata = _show_model(model)
    capabilities = metadata.get("capabilities")
    if capabilities is None:
        return _probe_chat_tool_support(model)
    return "tools" in capabilities


def build_tool_support_error(model: str) -> str:
    """Build a user-facing remediation message for non-tool-capable models."""
    recommended = ", ".join(RECOMMENDED_TOOL_MODELS)
    return (
        f"Configured Ollama chat model '{model}' does not support tool/function "
        "calling, which is required by the Google ADK orchestrator and agents in "
        "this application. Install and select an Ollama model with the 'tools' "
        f"capability, for example: ollama pull {RECOMMENDED_TOOL_MODELS[0]} "
        f"and set OLLAMA_CHAT_MODEL={RECOMMENDED_TOOL_MODELS[0]}. Other common "
        f"tool-capable choices include: {recommended}. Restart the API after "
        "changing the model."
    )


def assert_ollama_model_supports_adk_tools(model: str | None = None) -> None:
    """Validate that the configured chat model can be used by ADK agents.

    Raises:
        OllamaModelCapabilityError: if Ollama is reachable but the model lacks
            native tool/function-calling support.
        requests.HTTPError/ConnectionError/Timeout: for Ollama availability or
            model lookup failures. These are intentionally left distinct so the
            API can report whether Ollama itself is unavailable.
    """
    model_name = model or settings.ollama_chat_model
    if not ollama_model_supports_tools(model_name):
        raise OllamaModelCapabilityError(build_tool_support_error(model_name))
