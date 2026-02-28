"""
Integrated API endpoints demonstrating end-to-end flows
Connects voice interface, RAG engine, domain services, and impact tracker
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.integration_orchestrator import (
    IntegrationOrchestrator,
    VoiceQueryRequest,
    VoiceQueryResponse
)
from app.services.vector_store import VectorStore
from app.services.rag_engine import RAGEngine
from app.services.conversation_manager import ConversationManager
from app.schemas.integrated import (
    IntegratedVoiceQueryResponse,
    SchemeAccessRequest,
    SchemeApplicationRequest,
    JobDiscoveryRequest,
    HealthCheckRequest,
    IntegratedResponse
)
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/integrated", tags=["Integrated Flows"])
settings = get_settings()

# Global instances (in production, use dependency injection)
_orchestrator = None


def get_orchestrator(db: Session = Depends(get_db)) -> IntegrationOrchestrator:
    """Get or create integration orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        # Initialize components
        vector_store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/faiss_index"
        )
        
        rag_engine = RAGEngine(
            vector_store=vector_store,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            api_key=settings.openai_api_key if hasattr(settings, 'openai_api_key') else None
        )
        
        conversation_manager = ConversationManager(session_ttl_hours=24)
        
        _orchestrator = IntegrationOrchestrator(
            db=db,
            vector_store=vector_store,
            rag_engine=rag_engine,
            conversation_manager=conversation_manager
        )
    
    return _orchestrator


@router.post(
    "/voice-query",
    response_model=IntegratedVoiceQueryResponse,
    summary="End-to-end voice query processing",
    description="Process voice query through complete pipeline: STT → RAG → TTS with impact tracking"
)
async def process_voice_query(
    audio: UploadFile = File(..., description="Audio file with user query"),
    session_id: Optional[str] = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Process voice query end-to-end:
    1. Convert speech to text (STT)
    2. Process query through RAG engine
    3. Convert response to speech (TTS)
    4. Track interaction via Impact Tracker
    
    Returns both text and audio responses with conversation context.
    """
    try:
        # Validate audio file
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio file format"
            )
        
        # Read audio data
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty"
            )
        
        # Create request
        request = VoiceQueryRequest(
            audio_data=audio_data,
            user_id=str(current_user.user_id),
            session_id=session_id,
            language=language
        )
        
        # Process through orchestrator
        logger.info(f"Processing integrated voice query for user {current_user.user_id}")
        response = await orchestrator.process_voice_query(request)
        
        # Return response (audio as base64 for JSON compatibility)
        import base64
        audio_base64 = base64.b64encode(response.audio_answer).decode('utf-8')
        
        return IntegratedVoiceQueryResponse(
            text_query=response.text_query,
            text_answer=response.text_answer,
            audio_answer_base64=audio_base64,
            detected_language=response.detected_language,
            confidence=response.confidence,
            sources=response.sources,
            session_id=response.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in integrated voice query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice query: {str(e)}"
        )


@router.post(
    "/voice-query/audio",
    response_class=Response,
    summary="Get audio response for voice query",
    description="Same as /voice-query but returns audio directly instead of base64"
)
async def process_voice_query_audio(
    audio: UploadFile = File(..., description="Audio file with user query"),
    session_id: Optional[str] = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Process voice query and return audio response directly.
    Use this endpoint when you want to play the audio immediately.
    """
    try:
        # Validate and read audio
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio file format"
            )
        
        audio_data = await audio.read()
        
        # Create request
        request = VoiceQueryRequest(
            audio_data=audio_data,
            user_id=str(current_user.user_id),
            session_id=session_id,
            language=language
        )
        
        # Process through orchestrator
        response = await orchestrator.process_voice_query(request)
        
        # Return audio directly
        return Response(
            content=response.audio_answer,
            media_type="audio/mpeg",
            headers={
                "X-Text-Query": response.text_query,
                "X-Text-Answer": response.text_answer[:500],  # Truncate for header
                "X-Detected-Language": response.detected_language,
                "X-Session-ID": response.session_id,
                "Content-Disposition": f"attachment; filename=response_{response.detected_language}.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in integrated voice query audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice query: {str(e)}"
        )


@router.post(
    "/scheme/access",
    response_model=IntegratedResponse,
    summary="Track scheme access with impact tracking"
)
async def track_scheme_access(
    request: SchemeAccessRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Track when user accesses a scheme.
    Automatically records interaction in Impact Tracker.
    """
    try:
        orchestrator.track_scheme_access(
            user_id=str(current_user.user_id),
            scheme_id=request.scheme_id,
            scheme_name=request.scheme_name,
            language=request.language or "en"
        )
        
        return IntegratedResponse(
            success=True,
            message="Scheme access tracked successfully",
            data={"scheme_id": request.scheme_id}
        )
        
    except Exception as e:
        logger.error(f"Error tracking scheme access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking scheme access: {str(e)}"
        )


@router.post(
    "/scheme/apply",
    response_model=IntegratedResponse,
    summary="Track scheme application with outcome tracking"
)
async def track_scheme_application(
    request: SchemeApplicationRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Track when user applies for a scheme.
    Records successful outcome in Impact Tracker.
    """
    try:
        orchestrator.track_scheme_application(
            user_id=str(current_user.user_id),
            scheme_id=request.scheme_id,
            scheme_name=request.scheme_name
        )
        
        return IntegratedResponse(
            success=True,
            message="Scheme application tracked successfully",
            data={"scheme_id": request.scheme_id}
        )
        
    except Exception as e:
        logger.error(f"Error tracking scheme application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking scheme application: {str(e)}"
        )


@router.post(
    "/job/discover",
    response_model=IntegratedResponse,
    summary="Track job discovery with impact tracking"
)
async def track_job_discovery(
    request: JobDiscoveryRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Track when user discovers a job posting.
    Automatically records interaction in Impact Tracker.
    """
    try:
        orchestrator.track_job_discovery(
            user_id=str(current_user.user_id),
            job_id=request.job_id,
            job_title=request.job_title,
            language=request.language or "en"
        )
        
        return IntegratedResponse(
            success=True,
            message="Job discovery tracked successfully",
            data={"job_id": request.job_id}
        )
        
    except Exception as e:
        logger.error(f"Error tracking job discovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking job discovery: {str(e)}"
        )


@router.post(
    "/health/check",
    response_model=IntegratedResponse,
    summary="Track health check with impact tracking"
)
async def track_health_check(
    request: HealthCheckRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    """
    Track when user performs health symptom check.
    Automatically records interaction in Impact Tracker.
    """
    try:
        orchestrator.track_health_check(
            user_id=str(current_user.user_id),
            symptoms=request.symptoms,
            urgency_level=request.urgency_level,
            language=request.language or "en"
        )
        
        return IntegratedResponse(
            success=True,
            message="Health check tracked successfully",
            data={"symptoms_count": len(request.symptoms)}
        )
        
    except Exception as e:
        logger.error(f"Error tracking health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking health check: {str(e)}"
        )
