"""
Test Configuration for Backend (pytest)
Place this file at: tests/conftest.py
"""

import os
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock
from app.config import settings


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for tests."""
    return {
        "upload_dir": "/tmp/test_uploads",
        "chroma_dir": "/tmp/test_chroma",
        "ollama_base_url": "http://localhost:11434",
    }


@pytest.fixture
def mock_ollama_embed(monkeypatch):
    """Mock Ollama embedding calls."""
    def mock_embed(texts):
        # Return dummy embeddings
        return [[0.1 * i] * 384 for i in range(len(texts))]
    
    monkeypatch.setattr("app.tools.ollama_client.ollama_embed", mock_embed)
    return mock_embed


@pytest.fixture
def mock_ollama_chat(monkeypatch):
    """Mock Ollama chat calls."""
    def mock_chat(messages, model=None, stream=False):
        return {
            "message": {
                "content": "This is a mock response from Ollama."
            }
        }
    
    monkeypatch.setattr("app.tools.ollama_client.ollama_chat", mock_chat)
    return mock_chat


@pytest.fixture
def mock_vector_store(monkeypatch):
    """Mock ChromaDB vector store."""
    mock_store = MagicMock()
    mock_store.search.return_value = [
        {
            "text": "Sample chunk from document",
            "metadata": {
                "document_id": "test_doc",
                "document_name": "test.pdf",
                "page_number": 1,
            },
            "score": 0.95,
        }
    ]
    mock_store.add_chunks.return_value = None
    
    monkeypatch.setattr("app.tools.vector_store.vector_store", mock_store)
    return mock_store


@pytest.fixture
def mock_extract_text(monkeypatch):
    """Mock text extraction from documents."""
    def mock_extract(file_path, file_type):
        return ["Text from document unit 1", "Text from document unit 2"]
    
    monkeypatch.setattr("app.tools.extract_text.extract_text", mock_extract)
    return mock_extract


@pytest.fixture
def mock_chunk_text(monkeypatch):
    """Mock text chunking."""
    def mock_chunk(text_units):
        return [
            {
                "text": unit,
                "chunk_index": i,
                "page_number": 1,
                "section_title": "Introduction",
            }
            for i, unit in enumerate(text_units)
        ]
    
    monkeypatch.setattr("app.tools.chunk_text.chunk_text", mock_chunk)
    return mock_chunk


@pytest.fixture
def sample_document():
    """Fixture with sample document data."""
    return {
        "document_id": "doc_test_123",
        "document_name": "Sample.pdf",
        "file_type": "pdf",
        "user_id": "user_123",
        "status": "indexed",
        "chunk_count": 5,
    }


@pytest.fixture
def sample_chunks():
    """Fixture with sample document chunks."""
    return [
        {
            "text": "The renewal date is December 31, 2024.",
            "metadata": {
                "page_number": 5,
                "slide_number": None,
                "document_id": "doc_123",
            }
        },
        {
            "text": "The liability cap is $1,000,000.",
            "metadata": {
                "page_number": 8,
                "slide_number": None,
                "document_id": "doc_123",
            }
        },
    ]


@pytest.fixture
def sample_query_request():
    """Fixture with sample query request."""
    return {
        "user_id": "user_123",
        "message": "What is the renewal date?",
        "document_id": "doc_123",
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


# Test output configuration
def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on file location."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
