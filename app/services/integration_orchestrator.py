"""
Integration Orchestrator for BharatSahayak
Connects voice interface, RAG engine, domain services, and impact tracker
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

from app.services.voice_interface import get_stt_engine, get_tts_engine
from app.services.rag_engine import RAGEngine, ConversationContext
from app.services.conversation_manager import ConversationManager
from app.services.vector_store import VectorStore
from app.services.impact_tracker import ImpactTracker
from app.schemas.impact import InteractionEventCreate, OutcomeEventCreate, InteractionEventType, OutcomeEventType
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class VoiceQueryRequest:
    """Request for voice-based query"""
    audio_data: bytes
    user_id: str
    session_id: Optional[str] = None
    language: Optional[str] = None


@dataclass
class VoiceQueryResponse:
    """Response for voice-based query"""
    text_query: str
    text_answer: str
    audio_answer: bytes
    detected_language: str
    confidence: float
    sources: List[Dict[str, Any]]
    session_id: str


class IntegrationOrchestrator:
    """
    Orchestrates end-to-end integration of all BharatSahayak components
    
    Flow:
    1. Voice input → STT → Text query
    2. Text query → RAG Engine → Text response
    3. Text response → TTS → Audio response
    4. Track interaction and outcomes via Impact Tracker
    """
    
    def __init__(
        self,
        db: Session,
        vector_store: VectorStore,
        rag_engine: RAGEngine,
        conversation_manager: ConversationManager
    ):
        """
        Initialize Integration Orchestrator
        
        Args:
            db: Database session
            vector_store: Vector store for RAG
            rag_engine: RAG engine for query processing
            conversation_manager: Conversation manager for context
        """
        self.db = db
        self.vector_store = vector_store
        self.rag_engine = rag_engine
        self.conversation_manager = conversation_manager
        self.impact_tracker = ImpactTracker(db)
        
        # Initialize voice engines
        self.stt_engine = get_stt_engine()
        self.tts_engine = get_tts_engine()
        
        logger.info("Integration Orchestrator initialized")
    
    async def process_voice_query(
        self,
        request: VoiceQueryRequest
    ) -> VoiceQueryResponse:
        """
        Process end-to-end voice query
        
        Args:
            request: Voice query request with audio data
            
        Returns:
            VoiceQueryResponse with text and audio responses
        """
        try:
            # Step 1: Voice to Text (STT)
            logger.info(f"Processing voice query for user {request.user_id}")
            transcription = self.stt_engine.transcribe(
                audio_data=request.audio_data,
                language=request.language
            )
            
            text_query = transcription.text
            detected_language = transcription.detected_language
            
            logger.info(f"Transcribed query: '{text_query}' (language: {detected_language})")
            
            # Track voice interaction
            self._track_interaction(
                user_id=request.user_id,
                event_type=InteractionEventType.VOICE_INTERACTION,
                event_data={
                    "query": text_query,
                    "language": detected_language,
                    "confidence": transcription.confidence
                },
                language=detected_language
            )
            
            # Step 2: Get or create conversation context
            context = None
            session_id = request.session_id
            
            if session_id:
                context = self.conversation_manager.get_context(session_id)
            
            if not context:
                # Create new session
                session_id = self.conversation_manager.create_session(
                    user_id=request.user_id,
                    language=detected_language
                )
                context = self.conversation_manager.get_context(session_id)
            
            # Step 3: Process query through RAG engine
            logger.info(f"Processing query through RAG engine (session: {session_id})")
            rag_response = self.rag_engine.query(
                user_query=text_query,
                context=context,
                top_k=5,
                min_score=0.7
            )
            
            text_answer = rag_response.answer
            
            # Update conversation context
            self.conversation_manager.add_turn(
                session_id=session_id,
                user_message=text_query,
                assistant_message=text_answer
            )
            
            # Track query submission
            self._track_interaction(
                user_id=request.user_id,
                event_type=InteractionEventType.QUERY_SUBMITTED,
                event_data={
                    "query": text_query,
                    "answer_length": len(text_answer),
                    "sources_count": len(rag_response.sources),
                    "confidence": rag_response.confidence
                },
                language=detected_language
            )
            
            # Step 4: Text to Speech (TTS)
            logger.info(f"Synthesizing speech response in {detected_language}")
            audio_answer = self.tts_engine.synthesize(
                text=text_answer,
                language=detected_language
            )
            
            # Convert sources to dict format
            sources = [
                {
                    "doc_id": result.document.doc_id,
                    "content": result.document.content[:200],
                    "source": result.document.source,
                    "source_type": result.document.source_type,
                    "score": result.score
                }
                for result in rag_response.sources
            ]
            
            logger.info(f"Voice query processed successfully (session: {session_id})")
            
            return VoiceQueryResponse(
                text_query=text_query,
                text_answer=text_answer,
                audio_answer=audio_answer,
                detected_language=detected_language,
                confidence=rag_response.confidence,
                sources=sources,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Error processing voice query: {str(e)}")
            raise
    
    def track_scheme_access(
        self,
        user_id: str,
        scheme_id: str,
        scheme_name: str,
        language: str = "en"
    ):
        """Track when user accesses a scheme"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={
                "scheme_id": scheme_id,
                "scheme_name": scheme_name
            },
            language=language
        )
    
    def track_scheme_application(
        self,
        user_id: str,
        scheme_id: str,
        scheme_name: str
    ):
        """Track when user applies for a scheme"""
        self._track_outcome(
            user_id=user_id,
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={
                "scheme_id": scheme_id,
                "scheme_name": scheme_name
            }
        )
    
    def track_crop_advice(
        self,
        user_id: str,
        crop_recommendations: List[str],
        language: str = "en"
    ):
        """Track when farmer receives crop advice"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
            event_data={
                "recommendations": crop_recommendations,
                "count": len(crop_recommendations)
            },
            language=language
        )
    
    def track_fertilizer_advice(
        self,
        user_id: str,
        crop_name: str,
        language: str = "en"
    ):
        """Track when farmer receives fertilizer advice"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.FERTILIZER_ADVICE_REQUESTED,
            event_data={
                "crop_name": crop_name
            },
            language=language
        )
    
    def track_market_price_check(
        self,
        user_id: str,
        crop_name: str,
        prices_found: int,
        language: str = "en"
    ):
        """Track when farmer checks market prices"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.MARKET_PRICE_CHECKED,
            event_data={
                "crop_name": crop_name,
                "prices_found": prices_found
            },
            language=language
        )
    
    def track_job_discovery(
        self,
        user_id: str,
        job_id: str,
        job_title: str,
        language: str = "en"
    ):
        """Track when user discovers a job"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.JOB_DISCOVERED,
            event_data={
                "job_id": job_id,
                "job_title": job_title
            },
            language=language
        )
    
    def track_job_application(
        self,
        user_id: str,
        job_id: str,
        job_title: str
    ):
        """Track when user applies for a job"""
        self._track_outcome(
            user_id=user_id,
            outcome_type=OutcomeEventType.JOB_APPLIED,
            outcome_data={
                "job_id": job_id,
                "job_title": job_title
            }
        )
    
    def track_skill_program_view(
        self,
        user_id: str,
        program_id: str,
        program_name: str,
        language: str = "en"
    ):
        """Track when user views a skill program"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.SKILL_PROGRAM_VIEWED,
            event_data={
                "program_id": program_id,
                "program_name": program_name
            },
            language=language
        )
    
    def track_skill_enrollment(
        self,
        user_id: str,
        program_id: str,
        program_name: str
    ):
        """Track when user enrolls in a skill program"""
        self._track_outcome(
            user_id=user_id,
            outcome_type=OutcomeEventType.SKILL_ENROLLED,
            outcome_data={
                "program_id": program_id,
                "program_name": program_name
            }
        )
    
    def track_health_check(
        self,
        user_id: str,
        symptoms: List[str],
        urgency_level: str,
        language: str = "en"
    ):
        """Track when user performs health check"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.HEALTH_CHECK_PERFORMED,
            event_data={
                "symptoms": symptoms,
                "urgency_level": urgency_level
            },
            language=language
        )
    
    def track_facility_location(
        self,
        user_id: str,
        facility_type: str,
        facilities_found: int,
        language: str = "en"
    ):
        """Track when user locates health facilities"""
        self._track_interaction(
            user_id=user_id,
            event_type=InteractionEventType.FACILITY_LOCATED,
            event_data={
                "facility_type": facility_type,
                "facilities_found": facilities_found
            },
            language=language
        )
    
    def track_facility_visit(
        self,
        user_id: str,
        facility_id: str,
        facility_name: str
    ):
        """Track when user visits a health facility"""
        self._track_outcome(
            user_id=user_id,
            outcome_type=OutcomeEventType.FACILITY_VISITED,
            outcome_data={
                "facility_id": facility_id,
                "facility_name": facility_name
            }
        )
    
    def _track_interaction(
        self,
        user_id: str,
        event_type: InteractionEventType,
        event_data: Dict[str, Any],
        language: str = "en"
    ):
        """Internal method to track interaction events"""
        try:
            event = InteractionEventCreate(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                language=language
            )
            self.impact_tracker.record_interaction(event)
        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")
            # Don't fail the main operation if tracking fails
    
    def _track_outcome(
        self,
        user_id: str,
        outcome_type: OutcomeEventType,
        outcome_data: Dict[str, Any]
    ):
        """Internal method to track outcome events"""
        try:
            outcome = OutcomeEventCreate(
                user_id=user_id,
                outcome_type=outcome_type,
                outcome_data=outcome_data
            )
            self.impact_tracker.record_outcome(outcome)
        except Exception as e:
            logger.error(f"Error tracking outcome: {str(e)}")
            # Don't fail the main operation if tracking fails
