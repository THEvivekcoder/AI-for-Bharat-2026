"""Schemas for integrated API endpoints"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class IntegratedVoiceQueryResponse(BaseModel):
    """Response for integrated voice query"""
    text_query: str = Field(..., description="Transcribed text query")
    text_answer: str = Field(..., description="Text response from RAG engine")
    audio_answer_base64: str = Field(..., description="Audio response encoded as base64")
    detected_language: str = Field(..., description="Detected language code")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    session_id: str = Field(..., description="Conversation session ID")


class SchemeAccessRequest(BaseModel):
    """Request to track scheme access"""
    scheme_id: str = Field(..., description="Scheme UUID")
    scheme_name: str = Field(..., description="Scheme name")
    language: Optional[str] = Field("en", description="User's language")


class SchemeApplicationRequest(BaseModel):
    """Request to track scheme application"""
    scheme_id: str = Field(..., description="Scheme UUID")
    scheme_name: str = Field(..., description="Scheme name")


class JobDiscoveryRequest(BaseModel):
    """Request to track job discovery"""
    job_id: str = Field(..., description="Job posting UUID")
    job_title: str = Field(..., description="Job title")
    language: Optional[str] = Field("en", description="User's language")


class HealthCheckRequest(BaseModel):
    """Request to track health check"""
    symptoms: List[str] = Field(..., description="List of symptoms")
    urgency_level: str = Field(..., description="Urgency level from health advisor")
    language: Optional[str] = Field("en", description="User's language")


class IntegratedResponse(BaseModel):
    """Generic response for integrated endpoints"""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
