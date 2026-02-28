"""
Pydantic schemas for RAG and conversation endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request schema for /api/ask endpoint"""
    query: str = Field(..., description="User's question or query", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    language: str = Field("en", description="User's preferred language")
    top_k: int = Field(5, description="Number of documents to retrieve", ge=1, le=10)
    min_score: float = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class SourceInfo(BaseModel):
    """Information about a source document"""
    doc_id: str
    content: str
    source: str
    source_type: str
    score: float
    rank: int


class AskResponse(BaseModel):
    """Response schema for /api/ask endpoint"""
    answer: str
    sources: List[SourceInfo]
    confidence: float
    context_used: bool
    language: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateSessionRequest(BaseModel):
    """Request schema for /api/session/create endpoint"""
    user_id: str = Field(..., description="User identifier")
    language: str = Field("en", description="User's preferred language")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User profile data")


class CreateSessionResponse(BaseModel):
    """Response schema for /api/session/create endpoint"""
    session_id: str
    created_at: datetime
    language: str


class SessionStatsResponse(BaseModel):
    """Response schema for session statistics"""
    session_id: str
    user_id: str
    language: str
    num_turns: int
    created_at: str
    last_activity: str
    duration_minutes: float
    current_topic: Optional[str] = None


class DeleteSessionResponse(BaseModel):
    """Response schema for session deletion"""
    success: bool
    message: str
    session_id: str


class AddDocumentRequest(BaseModel):
    """Request schema for adding documents to knowledge base"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    source_type: str = Field("general", description="Type of source: official, verified, or general")


class AddDocumentsRequest(BaseModel):
    """Request schema for adding multiple documents"""
    documents: List[AddDocumentRequest]


class AddDocumentsResponse(BaseModel):
    """Response schema for adding documents"""
    success: bool
    num_documents_added: int
    message: str


class VectorStoreStatsResponse(BaseModel):
    """Response schema for vector store statistics"""
    total_documents: int
    index_size: int
    embedding_dimension: int
    embedding_model: str
    source_type_distribution: Dict[str, int]
