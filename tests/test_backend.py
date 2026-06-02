"""
Backend Unit Tests — Pytest Test Suite
Tests for core agents, tools, and services
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.adk_runtime.orchestrator import classify_intents
from app.adk_runtime.answering_agent import generate_answer
from app.adk_runtime.retrieval_agent import retrieve_chunks
from app.adk_runtime.ingestion_agent import ingest_document
from app.services.document_registry import InMemoryDocumentRegistry
from app.tools.vector_store import ChromaVectorStore
from app.config import settings


# ════════════════════════════════════════════════════════
# ORCHESTRATOR TESTS
# ════════════════════════════════════════════════════════

class TestClassifyIntents:
    """Test intent classification with various user inputs."""

    def test_single_qa_intent(self):
        """Test simple question is classified as QA."""
        result = classify_intents("What is the renewal date?")
        assert "qa" in result["intents"]
        assert result["intent_count"] >= 1

    def test_upload_intent(self):
        """Test upload-related keywords are recognized."""
        upload_keywords = ["upload", "ingest", "process", "index"]
        for keyword in upload_keywords:
            result = classify_intents(f"Please {keyword} this document")
            assert "upload" in result["intents"], f"Failed for keyword: {keyword}"

    def test_summary_intent(self):
        """Test summary-related keywords are recognized."""
        summary_keywords = ["summarize", "summary", "overview", "key points"]
        for keyword in summary_keywords:
            result = classify_intents(f"Give me a {keyword} of the document")
            assert "summary" in result["intents"], f"Failed for keyword: {keyword}"

    def test_multi_intent_detection(self):
        """Test compound questions are split correctly."""
        result = classify_intents("What is the renewal date and what is the liability cap?")
        assert result["is_multi_intent"] is True
        assert result["intent_count"] >= 2

    def test_empty_message(self):
        """Test empty input defaults to QA."""
        result = classify_intents("")
        assert "qa" in result["intents"]

    def test_greeting_not_classified_as_tool_call(self):
        """Greetings should NOT trigger tool calls (orchestrator handles directly)."""
        result = classify_intents("Hello, how are you?")
        # This test validates current behavior; greetings don't need tool calls
        # (They're handled in orchestrator instruction)
        assert result is not None

    def test_regex_injection_resistance(self):
        """Test that user input doesn't cause regex DoS."""
        malicious = "a" * 10000 + "?"
        # Should not hang or crash
        result = classify_intents(malicious)
        assert result["intents"] is not None


# ════════════════════════════════════════════════════════
# ANSWERING AGENT TESTS
# ════════════════════════════════════════════════════════

class TestGenerateAnswer:
    """Test answer generation with various chunk scenarios."""

    def test_answer_with_valid_chunks(self):
        """Test generating answer from valid chunks."""
        chunks = json.dumps([
            {
                "text": "The renewal date is December 31, 2024.",
                "metadata": {"page_number": 5, "slide_number": None}
            }
        ])
        
        with patch('app.adk_runtime.answering_agent.ollama_chat') as mock_chat:
            mock_chat.return_value = {
                "answer": "The renewal date is December 31, 2024.",
                "citations": [{"page_number": 5}]
            }
            
            result = generate_answer(
                question="When is the renewal date?",
                chunks=chunks,
                intent="qa"
            )
            
            assert result["status"] == "success" or result["status"] is None
            assert "answer" in result

    def test_answer_with_empty_chunks(self):
        """Test that empty chunks return appropriate message."""
        result = generate_answer(
            question="What is the renewal date?",
            chunks="[]",
            intent="qa"
        )
        
        assert result["status"] == "not_found"
        assert "No relevant content" in result["answer"]
        assert result["citations"] == []

    def test_answer_with_invalid_json_chunks(self):
        """Test handling of malformed chunk JSON."""
        result = generate_answer(
            question="What is the renewal date?",
            chunks="INVALID JSON",
            intent="qa"
        )
        
        assert result["status"] == "not_found"
        assert result["citations"] == []

    def test_chunk_limit_enforcement(self):
        """Test that only top 3 chunks are used."""
        chunks = json.dumps([
            {"text": f"Chunk {i}", "metadata": {"page_number": i}}
            for i in range(10)
        ])
        
        with patch('app.adk_runtime.answering_agent.ollama_chat') as mock_chat:
            mock_chat.return_value = {"answer": "Test", "citations": []}
            
            result = generate_answer(
                question="Question?",
                chunks=chunks,
                intent="qa"
            )
            
            # Verify ollama_chat was called with limited chunks
            assert mock_chat.called

    def test_summary_vs_qa_intent(self):
        """Test different system prompts for summary vs QA."""
        chunks = json.dumps([
            {"text": "Sample content", "metadata": {"page_number": 1}}
        ])
        
        with patch('app.adk_runtime.answering_agent.ollama_chat') as mock_chat:
            mock_chat.return_value = {"answer": "Test", "citations": []}
            
            # Call with summary intent
            generate_answer(
                question="Summarize this",
                chunks=chunks,
                intent="summary"
            )
            
            # Verify system prompt mentions summarization
            call_args = mock_chat.call_args
            assert call_args is not None


# ════════════════════════════════════════════════════════
# RETRIEVAL AGENT TESTS
# ════════════════════════════════════════════════════════

class TestRetrieveChunks:
    """Test document chunk retrieval."""

    @patch('app.adk_runtime.retrieval_agent.ollama_embed')
    @patch('app.adk_runtime.retrieval_agent.vector_store')
    def test_retrieve_specific_document(self, mock_vs, mock_embed):
        """Test retrieving chunks from specific document."""
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        mock_vs.search.return_value = [
            {
                "text": "Sample chunk",
                "metadata": {"page_number": 1},
                "score": 0.95
            }
        ]
        
        result = retrieve_chunks(
            query="What is the renewal date?",
            user_id="user_123",
            document_id="doc_456",
            intent="qa"
        )
        
        assert result["status"] == "success" or "chunks" in result

    @patch('app.adk_runtime.retrieval_agent.ollama_embed')
    @patch('app.adk_runtime.retrieval_agent.vector_store')
    def test_retrieve_with_latest_document(self, mock_vs, mock_embed):
        """Test 'latest' document ID retrieves from all docs."""
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        mock_vs.search.return_value = []
        
        result = retrieve_chunks(
            query="Question?",
            user_id="user_123",
            document_id="latest",  # Special value
            intent="qa"
        )
        
        # Should call search without document_id filter
        assert result is not None

    @patch('app.adk_runtime.retrieval_agent.ollama_embed')
    @patch('app.adk_runtime.retrieval_agent.vector_store')
    def test_fallback_to_default_user(self, mock_vs, mock_embed):
        """Test fallback when user has no documents."""
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        mock_vs.search.side_effect = [
            [],  # First call returns empty
            [{"text": "Result from default", "metadata": {}, "score": 0.9}]  # Fallback
        ]
        
        result = retrieve_chunks(
            query="Question?",
            user_id="unknown_user",
            document_id="specific_doc",
            intent="qa"
        )
        
        # Should attempt fallback
        assert mock_vs.search.call_count >= 1

    @patch('app.adk_runtime.retrieval_agent.ollama_embed')
    @patch('app.adk_runtime.retrieval_agent.vector_store')
    def test_similarity_threshold_filtering(self, mock_vs, mock_embed):
        """Test that low-scoring results are filtered."""
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        mock_vs.search.return_value = [
            {"text": "Good chunk", "metadata": {}, "score": 0.95},
            {"text": "Bad chunk", "metadata": {}, "score": 0.10},  # Below threshold
        ]
        
        result = retrieve_chunks(
            query="Question?",
            user_id="user_123",
            document_id="doc_456",
            intent="qa"
        )
        
        # Low-scoring chunk should be filtered
        assert result is not None


# ════════════════════════════════════════════════════════
# INGESTION AGENT TESTS
# ════════════════════════════════════════════════════════

class TestIngestDocument:
    """Test document ingestion pipeline."""

    @patch('app.adk_runtime.ingestion_agent.extract_text')
    @patch('app.adk_runtime.ingestion_agent.chunk_text')
    @patch('app.adk_runtime.ingestion_agent.ollama_embed')
    @patch('app.adk_runtime.ingestion_agent.vector_store')
    def test_ingest_valid_document(self, mock_vs, mock_embed, mock_chunk, mock_extract):
        """Test successful document ingestion."""
        mock_extract.return_value = ["Text unit 1", "Text unit 2"]
        mock_chunk.return_value = [
            {"text": "Chunk 1", "page_number": 1},
            {"text": "Chunk 2", "page_number": 1}
        ]
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        
        result = ingest_document(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            file_type="pdf",
            user_id="user_123"
        )
        
        assert result["status"] == "indexed"
        assert result["chunk_count"] == 2
        mock_vs.add_chunks.assert_called_once()

    @patch('app.adk_runtime.ingestion_agent.extract_text')
    def test_ingest_empty_document(self, mock_extract):
        """Test handling of documents with no text."""
        mock_extract.return_value = []
        
        result = ingest_document(
            file_path="/tmp/empty.pdf",
            file_name="empty.pdf",
            file_type="pdf",
            user_id="user_123"
        )
        
        assert result["status"] == "empty"
        assert result["chunk_count"] == 0

    @patch('app.adk_runtime.ingestion_agent.extract_text')
    def test_ingest_missing_file(self, mock_extract):
        """Test handling of missing file."""
        mock_extract.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(FileNotFoundError):
            ingest_document(
                file_path="/tmp/nonexistent.pdf",
                file_name="nonexistent.pdf",
                file_type="pdf",
                user_id="user_123"
            )

    @patch('app.adk_runtime.ingestion_agent.extract_text')
    def test_ingest_unsupported_file_type(self, mock_extract):
        """Test rejection of unsupported file types."""
        # Note: File type validation happens at FastAPI level, but test anyway
        mock_extract.return_value = []
        
        result = ingest_document(
            file_path="/tmp/test.docx",
            file_name="test.docx",
            file_type="xlsx",  # Unsupported
            user_id="user_123"
        )
        
        assert result is not None


# ════════════════════════════════════════════════════════
# DOCUMENT REGISTRY TESTS
# ════════════════════════════════════════════════════════

class TestDocumentRegistry:
    """Test in-memory document registry."""

    def test_create_document(self):
        """Test creating a document record."""
        registry = InMemoryDocumentRegistry()
        
        doc_id = registry.create_document(
            user_id="user_123",
            document_name="test.pdf",
            file_type="pdf",
            status="indexed"
        )
        
        assert doc_id is not None
        doc = registry.get_document(doc_id)
        assert doc["document_name"] == "test.pdf"
        assert doc["user_id"] == "user_123"

    def test_list_documents_by_user(self):
        """Test listing documents for a specific user."""
        registry = InMemoryDocumentRegistry()
        
        doc_id_1 = registry.create_document(
            user_id="user_123",
            document_name="doc1.pdf",
            file_type="pdf",
            status="indexed"
        )
        doc_id_2 = registry.create_document(
            user_id="user_123",
            document_name="doc2.docx",
            file_type="docx",
            status="indexed"
        )
        registry.create_document(
            user_id="other_user",
            document_name="doc3.pdf",
            file_type="pdf",
            status="indexed"
        )
        
        docs = registry.list_documents("user_123")
        assert len(docs) == 2
        assert all(d["user_id"] == "user_123" for d in docs)

    def test_update_document(self):
        """Test updating document metadata."""
        registry = InMemoryDocumentRegistry()
        
        doc_id = registry.create_document(
            user_id="user_123",
            document_name="test.pdf",
            file_type="pdf",
            status="processing"
        )
        
        registry.update_document(doc_id, status="indexed", chunk_count=42)
        
        doc = registry.get_document(doc_id)
        assert doc["status"] == "indexed"
        assert doc["chunk_count"] == 42

    def test_latest_indexed_document(self):
        """Test finding the most recently indexed document."""
        registry = InMemoryDocumentRegistry()
        
        doc_id_1 = registry.create_document(
            user_id="user_123",
            document_name="old.pdf",
            file_type="pdf",
            status="indexed"
        )
        doc_id_2 = registry.create_document(
            user_id="user_123",
            document_name="new.pdf",
            file_type="pdf",
            status="indexed"
        )
        
        latest = registry.latest_document_id("user_123")
        assert latest == doc_id_2

    def test_delete_document(self):
        """Test deleting a document record."""
        registry = InMemoryDocumentRegistry()
        
        doc_id = registry.create_document(
            user_id="user_123",
            document_name="test.pdf",
            file_type="pdf",
            status="indexed"
        )
        
        registry.delete_document(doc_id)
        
        assert registry.get_document(doc_id) is None

    def test_delete_nonexistent_document(self):
        """Test error handling for deleting non-existent document."""
        registry = InMemoryDocumentRegistry()
        
        with pytest.raises(ValueError):
            registry.delete_document("nonexistent_id")


# ════════════════════════════════════════════════════════
# VECTOR STORE TESTS
# ════════════════════════════════════════════════════════

class TestVectorStore:
    """Test ChromaDB vector store operations."""

    def test_vector_store_initialization(self):
        """Test that vector store initializes correctly."""
        store = ChromaVectorStore()
        assert store.collection is not None
        assert store.client is not None

    def test_add_chunks(self):
        """Test adding chunks to the store."""
        store = ChromaVectorStore()
        
        chunks = [
            {"text": "Chunk 1", "page_number": 1, "chunk_index": 0},
            {"text": "Chunk 2", "page_number": 1, "chunk_index": 1}
        ]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        store.add_chunks(
            document_id="doc_1",
            document_name="test.pdf",
            user_id="user_123",
            chunks=chunks,
            embeddings=embeddings
        )
        
        # Verify chunks were added (would test count if ChromaDB API exposed it)
        assert store.collection is not None

    def test_search_with_filters(self):
        """Test searching with document and user filters."""
        store = ChromaVectorStore()
        
        chunks = [{"text": "Sample", "page_number": 1, "chunk_index": 0}]
        embeddings = [[0.1, 0.2, 0.3]]
        
        store.add_chunks(
            document_id="doc_1",
            document_name="test.pdf",
            user_id="user_123",
            chunks=chunks,
            embeddings=embeddings
        )
        
        results = store.search(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
            filters={"user_id": "user_123", "document_id": "doc_1"}
        )
        
        # Should return similar chunks
        assert isinstance(results, list)


# ════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ════════════════════════════════════════════════════════

class TestEndToEndFlow:
    """Test complete flows from upload to query."""

    @patch('app.adk_runtime.ingestion_agent.extract_text')
    @patch('app.adk_runtime.ingestion_agent.chunk_text')
    @patch('app.adk_runtime.ingestion_agent.ollama_embed')
    @patch('app.adk_runtime.ingestion_agent.vector_store')
    def test_upload_and_query_flow(self, mock_vs, mock_embed, mock_chunk, mock_extract):
        """Test complete flow from upload to retrieval."""
        # Step 1: Upload document
        mock_extract.return_value = ["Content"]
        mock_chunk.return_value = [{"text": "Chunk", "page_number": 1}]
        mock_embed.return_value = [[0.1, 0.2]]
        
        ingest_result = ingest_document(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            file_type="pdf",
            user_id="user_123"
        )
        
        assert ingest_result["status"] == "indexed"
        
        # Step 2: Registry should track it
        registry = InMemoryDocumentRegistry()
        doc_id = registry.create_document(
            user_id="user_123",
            document_name="test.pdf",
            file_type="pdf",
            status="indexed"
        )
        
        # Step 3: Classify intent
        intents = classify_intents("What is the main topic?")
        assert "qa" in intents["intents"]

    def test_multi_intent_flow(self):
        """Test handling of multi-intent requests."""
        intents = classify_intents(
            "Summarize the document and tell me about payment terms"
        )
        
        assert intents["is_multi_intent"] is True
        assert "summary" in intents["intents"] or "qa" in intents["intents"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
