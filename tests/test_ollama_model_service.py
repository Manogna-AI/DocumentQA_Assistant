from unittest.mock import Mock, patch

import pytest

from app.services.ollama_model_service import (
    OllamaModelCapabilityError,
    assert_ollama_model_supports_adk_tools,
    build_tool_support_error,
    is_ollama_tool_support_error,
    ollama_model_supports_tools,
)


def test_ollama_model_supports_tools_from_show_capabilities():
    ollama_model_supports_tools.cache_clear()
    response = Mock()
    response.json.return_value = {"capabilities": ["completion", "tools"]}
    response.raise_for_status.return_value = None

    with patch("app.services.ollama_model_service.requests.post", return_value=response):
        assert ollama_model_supports_tools("llama3.1") is True


def test_assert_raises_clear_message_for_non_tool_model():
    ollama_model_supports_tools.cache_clear()
    response = Mock()
    response.json.return_value = {"capabilities": ["completion"]}
    response.raise_for_status.return_value = None

    with patch("app.services.ollama_model_service.requests.post", return_value=response):
        with pytest.raises(OllamaModelCapabilityError) as exc_info:
            assert_ollama_model_supports_adk_tools("orca-mini:3b")

    message = str(exc_info.value)
    assert "orca-mini:3b" in message
    assert "Google ADK orchestrator" in message
    assert "OLLAMA_CHAT_MODEL=llama3.1" in message


def test_tool_support_error_recommends_ollama_model_change():
    message = build_tool_support_error("orca-mini:3b")

    assert "ollama pull llama3.1" in message
    assert "tools" in message


def test_runtime_tool_error_detection_walks_exception_chain():
    root = RuntimeError('{"error":"registry.ollama.ai/library/orca-mini:3b does not support tools"}')
    wrapped = RuntimeError("litellm.APIConnectionError: Ollama_chatException")
    wrapped.__cause__ = root

    assert is_ollama_tool_support_error(wrapped) is True


def test_runtime_tool_error_detection_ignores_unrelated_errors():
    assert is_ollama_tool_support_error(RuntimeError("connection timed out")) is False


def test_ollama_model_supports_tools_falls_back_to_direct_probe_when_show_lacks_capabilities():
    ollama_model_supports_tools.cache_clear()
    show_response = Mock()
    show_response.json.return_value = {}
    show_response.raise_for_status.return_value = None
    probe_response = Mock(status_code=400, text='{"error":"model does not support tools"}')

    with patch(
        "app.services.ollama_model_service.requests.post",
        side_effect=[show_response, probe_response],
    ):
        assert ollama_model_supports_tools("orca-mini:3b") is False
