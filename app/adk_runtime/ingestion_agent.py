"""
Agent 1: Document Ingestion Agent
Tools:
  - ingest_document: For FastAPI uploads (file already saved to disk)
  - ingest_from_artifact: For ADK Web UI uploads (file is an artifact in session)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
import tempfile
from app.config import settings
from google.adk.agents import Agent
from google.adk.tools import ToolContext

os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_base_url)
MODEL = f"ollama_chat/{settings.ollama_chat_model}"
#MODEL = "gemini-2.0-flash"

# ── Tool 1: For FastAPI uploads (file already on disk) ──

def ingest_document(
    file_path: str,
    file_name: str = "",
    file_type: str = "pdf",
    user_id: str = "default",
    document_id: str = "",
) -> dict:
    """Accept a document upload, extract text, chunk content,
    generate embeddings via Ollama, and store in ChromaDB vector store.

    Args:
        file_path: Path to the uploaded document file on disk.
        file_name: Original filename of the document.
        file_type: File format - one of 'pdf', 'docx', 'pptx'.
        user_id: ID of the uploading user.
        document_id: Unique identifier for this document.

    Returns:
        dict with status, document_id, document_name, chunk_count, message.
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    from pathlib import Path as P
    from app.tools.extract_text import extract_text
    from app.tools.chunk_text import chunk_text
    from app.tools.ollama_client import ollama_embed
    from app.tools.vector_store import vector_store
    import logging
    
    logger = logging.getLogger(__name__)

    if not file_name:
        file_name = P(file_path).name
    if not document_id:
        document_id = file_name

    # ✓ VALIDATION 1: File exists
    file_path_obj = P(file_path)
    if not file_path_obj.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(f"[ingest_document] {error_msg}")
        return {
            "status": "error",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": 0,
            "message": error_msg,
        }
    
    # ✓ VALIDATION 2: Path is a file, not directory
    if not file_path_obj.is_file():
        error_msg = f"Path is not a file: {file_path}"
        logger.error(f"[ingest_document] {error_msg}")
        return {
            "status": "error",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": 0,
            "message": error_msg,
        }
    
    # ✓ VALIDATION 3: File is readable
    if not file_path_obj.is_readable():
        error_msg = f"File is not readable: {file_path}"
        logger.error(f"[ingest_document] {error_msg}")
        return {
            "status": "error",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": 0,
            "message": error_msg,
        }
    
    # ✓ VALIDATION 4: File size check (redundant with FastAPI but defensive)
    file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
    # ✓ Use centralized config for max file size
    max_size = settings.max_file_size_mb
    if file_size_mb > max_size:
        error_msg = f"File exceeds max size: {file_size_mb:.1f}MB > {max_size}MB"
        logger.error(f"[ingest_document] {error_msg}")
        return {
            "status": "error",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": 0,
            "message": error_msg,
        }

    logger.info(
        f"[ingest_document] Starting ingestion for {file_name} "
        f"({file_type}, {file_size_mb:.1f}MB, user={user_id})"
    )

    try:
        text_units = extract_text(file_path=file_path, file_type=file_type)
        if not text_units:
            logger.info(f"[ingest_document] No text extracted from {file_name}")
            return {
                "status": "empty",
                "document_id": document_id,
                "document_name": file_name,
                "chunk_count": 0,
                "message": "No text content found in document.",
            }

        chunks = chunk_text(text_units=text_units)
        if not chunks:
            logger.warning(f"[ingest_document] No chunks generated from {file_name}")
            return {
                "status": "indexed",
                "document_id": document_id,
                "document_name": file_name,
                "chunk_count": 0,
                "message": "Document has no readable content.",
            }

        logger.info(f"[ingest_document] Generated {len(chunks)} chunks from {file_name}")

        embeddings = ollama_embed([c["text"] for c in chunks])
        vector_store.add_chunks(
            document_id=document_id,
            document_name=file_name,
            user_id=user_id,
            chunks=chunks,
            embeddings=embeddings,
        )
        
        logger.info(
            f"[ingest_document] Successfully indexed {file_name} "
            f"with {len(chunks)} chunks"
        )
        
        return {
            "status": "indexed",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": len(chunks),
            "message": f"Successfully indexed {len(chunks)} chunks from {file_name}.",
        }
        
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.exception(f"[ingest_document] {error_msg} for {file_name}")
        return {
            "status": "error",
            "document_id": document_id,
            "document_name": file_name,
            "chunk_count": 0,
            "message": error_msg,
        }


# ── Tool 2: For ADK Web UI uploads (file is an artifact) ──

async def ingest_from_artifact(
    filename: str,
    tool_context: ToolContext,
) -> dict:
    """Process a document that was uploaded through the ADK Web UI.
    The file is stored as an artifact in the session. This tool loads
    the artifact, saves it to a temp file, then runs the ingestion pipeline.

    Args:
        filename: Name of the uploaded file artifact (e.g., 'report.pdf').
        tool_context: ADK tool context for accessing artifacts.

    Returns:
        dict with status, document_id, document_name, chunk_count.
    """
    from app.tools.extract_text import extract_text
    from app.tools.chunk_text import chunk_text
    from app.tools.ollama_client import ollama_embed
    from app.tools.vector_store import vector_store

    # Step 1: Load artifact from session
    artifact = await tool_context.load_artifact(filename=filename)
    if not artifact or not artifact.inline_data:
        # Try listing available artifacts
        available = await tool_context.list_artifacts()
        if available:
            return {
                "status": "error",
                "message": f"Artifact '{filename}' not found. Available: {available}",
            }
        return {
            "status": "error",
            "message": "No uploaded files found. Please upload a document first.",
        }

    # Step 2: Determine file type from mime_type
    mime = artifact.inline_data.mime_type or ""
    file_type_map = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    }
    file_type = file_type_map.get(mime, "")
    if not file_type:
        # Try to guess from filename extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in ("pdf", "docx", "pptx"):
            file_type = ext
        else:
            return {
                "status": "error",
                "message": f"Unsupported file type: {mime}. Supported: PDF, DOCX, PPTX.",
            }

    # Step 3: Save artifact bytes to temp file
    suffix = f".{file_type}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(artifact.inline_data.data)
        tmp_path = tmp.name

    try:
        # Step 4: Run ingestion pipeline
        text_units = extract_text(file_path=tmp_path, file_type=file_type)
        if not text_units:
            return {"status": "empty", "document_id": filename,
                    "document_name": filename, "chunk_count": 0,
                    "message": "No text content found in document."}

        chunks = chunk_text(text_units=text_units)
        if not chunks:
            return {"status": "indexed", "document_id": filename,
                    "document_name": filename, "chunk_count": 0}

        embeddings = ollama_embed([c["text"] for c in chunks])

        user_id = "default"
        vector_store.add_chunks(
            document_id=filename, document_name=filename,
            user_id=user_id, chunks=chunks, embeddings=embeddings,
        )
        return {"status": "indexed", "document_id": filename,
                "document_name": filename, "chunk_count": len(chunks),
                "message": f"Successfully indexed {len(chunks)} chunks from {filename}."}
    finally:
        # Cleanup temp file
        os.unlink(tmp_path)


# ── Agent Definition (both tools available) ──

ingestion_agent = Agent(
    name="ingestion_agent",
    model=MODEL,
    description=(
        "Document Ingestion Agent — Accepts document uploads (PDF, PPTX, DOCX) "
        "from both the FastAPI API and the ADK Web UI. Extracts text, chunks "
        "content, generates embeddings, and stores in ChromaDB."
    ),
    instruction=(
        "You are the Document Ingestion Agent.\n\n"
        "You have TWO tools:\n\n"
        "1. ingest_document — Use when a FILE PATH is provided\n"
        "   (e.g., 'Upload document at storage/uploads/report.pdf')\n\n"
        "2. ingest_from_artifact — Use when a file was UPLOADED in the chat\n"
        "   (e.g., user attached a file in the ADK Web UI)\n"
        "   First call list_artifacts or check the filename from the user message.\n\n"
        "DECISION LOGIC:\n"
        "- If message contains a file_path → use ingest_document\n"
        "- If message mentions an uploaded/attached file → use ingest_from_artifact\n"
        "- If unsure, try ingest_from_artifact with the filename\n\n"
        "After processing, report: document_name, status, chunk_count."
    ),
    tools=[ingest_document, ingest_from_artifact],
    output_key="ingestion_result",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)