"""
Centralised application configuration.
All hardcoded values are now configurable via environment variables or .env.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────
    app_name: str = "google-adk-ollama-docqa"
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]

    # ── File upload ──────────────────────────────────────────
    upload_dir: str = "storage/uploads"
    max_file_size_mb: int = 50
    allowed_file_types: set[str] = {"pdf", "docx", "pptx"}

    # ── Ollama ────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "all-minilm"
    ollama_chat_model: str = "orca-mini:3b"
    ollama_embed_batch_size: int = 10
    ollama_request_timeout: int = 180
    ollama_max_retries: int = 3
    ollama_startup_check_timeout: int = 5  # Check if Ollama is running at startup
    ollama_health_check_timeout: int = 3   # Quick health check timeout

    #Gemini Model
    gemini_model: str = "gemini-2.0-flash"

    # ── Chunking ─────────────────────────────────────────────
    chunk_size_chars: int = 800
    overlap_chars: int = 100

    # ── Vector store ─────────────────────────────────────────
    chroma_dir: str = "storage/chroma"
    chroma_collection_name: str = "document_chunks"

    # ── Retrieval ────────────────────────────────────────────
    top_k_initial: int = 3
    top_k_summary: int = 5
    min_similarity_score: float = 0.25
    
    # ── QA Response Processing ───────────────────────────────
    qa_max_chunk_count: int = 3      # Max chunks to include in QA response
    qa_max_chunk_chars: int = 800    # Max chars per chunk in QA response
    text_preview_chars: int = 120    # Max chars for section titles/previews
    log_message_preview_chars: int = 50  # Chars to show in logs
    
    # ── Input Validation ─────────────────────────────────────
    max_user_message_length: int = 5000  # Max user message length (5KB)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
