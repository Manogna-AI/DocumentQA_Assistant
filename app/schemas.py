"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class Intent(str, Enum):
    UPLOAD = "upload"
    QA = "qa"
    SUMMARY = "summary"
    DOC_CONTEXT = "doc_context"
    UNKNOWN = "unknown"


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    file_type: str
    status: str
    chunk_count: int
    message: str = ""


class QueryRequest(BaseModel):
    user_id: str
    message: str
    document_id: Optional[str] = None
    use_latest: bool = True


class Citation(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    section_title: Optional[str] = None
    snippet: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentInfo(BaseModel):
    document_id: str
    document_name: str
    file_type: str
    status: str
    chunk_count: int
    created_at: str
    updated_at: str
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    user_id: str
    documents: List[DocumentInfo] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
