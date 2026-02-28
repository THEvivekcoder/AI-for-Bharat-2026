"""
RAG and Conversation API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from datetime import datetime

from app.schemas.rag import (
    AskRequest,
    AskResponse,
    SourceInfo,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionStatsResponse,
    DeleteSessionResponse,
    AddDocumentRequest,
    AddDocumentsRequest,
    AddDocumentsResponse,
    VectorStoreStatsResponse
)
from app.services.vector_store import VectorStore, Document
from app.services.rag_engine import RAGEngine
from app.services.conversation_manager import ConversationManager
from app.dependencies import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api")
settings = get_settings()

# Initialize services (in production, use dependency injection)
vector_store = None
rag_engine = None
conversation_manager = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance"""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/faiss_index"
        )
    return vector_store


def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine instance"""
    global rag_engine
    if rag_engine is None:
        vs = get_vector_store()
        rag_engine = RAGEngine(
            vector_store=vs,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            api_key=settings.openai_api_key if hasattr(settings, 'openai_api_key') else None
        )
    return rag_engine


def get_conversation_manager() -> ConversationManager:
    """Get or create conversation manager instance"""
    global conversation_manager
    if conversation_manager is None:
        conversation_manager = ConversationManager(session_ttl_hours=24)
    return conversation_manager


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Submit a query and receive an AI-generated response
    
    This endpoint uses RAG (Retrieval-Augmented Generation) to:
    1. Retrieve relevant documents from the knowledge base
    2. Generate a contextual response using an LLM
    3. Maintain conversation context if session_id is provided
    """
    try:
        engine = get_rag_engine()
        conv_manager = get_conversation_manager()
        
        # Get conversation context if session provided
        context = None
        if request.session_id:
            context = conv_manager.get_context(request.session_id)
            if context is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} not found or expired"
                )
        
        # Process query
        response = engine.query(
            user_query=request.query,
            context=context,
            top_k=request.top_k,
            min_score=request.min_score
        )
        
        # Update conversation context if session exists
        if context:
            conv_manager.add_turn(
                session_id=request.session_id,
                user_message=request.query,
                assistant_message=response.answer
            )
        
        # Convert sources to response format
        sources = [
            SourceInfo(
                doc_id=result.document.doc_id,
                content=result.document.content[:500],  # Truncate for response
                source=result.document.source,
                source_type=result.document.source_type,
                score=result.score,
                rank=result.rank
            )
            for result in response.sources
        ]
        
        return AskResponse(
            answer=response.answer,
            sources=sources,
            confidence=response.confidence,
            context_used=response.context_used,
            language=response.language,
            session_id=request.session_id,
            metadata=response.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/session/create", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Create a new conversation session
    
    Sessions maintain conversation context across multiple queries,
    enabling follow-up questions and contextual understanding.
    """
    try:
        conv_manager = get_conversation_manager()
        
        session_id = conv_manager.create_session(
            user_id=request.user_id,
            language=request.language,
            user_profile=request.user_profile
        )
        
        return CreateSessionResponse(
            session_id=session_id,
            created_at=datetime.utcnow(),
            language=request.language
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )


@router.delete("/session/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Clear conversation history for a session
    
    This deletes all conversation history and context for the specified session.
    """
    try:
        conv_manager = get_conversation_manager()
        
        success = conv_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return DeleteSessionResponse(
            success=True,
            message="Session deleted successfully",
            session_id=session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting session: {str(e)}"
        )


@router.get("/session/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    session_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get statistics about a conversation session
    
    Returns information about session duration, number of turns, and activity.
    """
    try:
        conv_manager = get_conversation_manager()
        
        stats = conv_manager.get_session_stats(session_id)
        
        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return SessionStatsResponse(**stats)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session stats: {str(e)}"
        )


@router.post("/documents/add", response_model=AddDocumentsResponse)
async def add_documents(
    request: AddDocumentsRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Add documents to the knowledge base
    
    This endpoint allows administrators to add new documents to the vector store
    for use in RAG responses. Requires authentication.
    """
    try:
        vs = get_vector_store()
        
        # Convert request documents to Document objects
        documents = [
            Document(
                doc_id=doc.doc_id,
                content=doc.content,
                metadata=doc.metadata,
                source=doc.source,
                source_type=doc.source_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for doc in request.documents
        ]
        
        # Add to vector store
        vs.add_documents(documents)
        
        # Save index
        vs.save_index()
        
        return AddDocumentsResponse(
            success=True,
            num_documents_added=len(documents),
            message=f"Successfully added {len(documents)} documents to knowledge base"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding documents: {str(e)}"
        )


@router.get("/documents/stats", response_model=VectorStoreStatsResponse)
async def get_vector_store_stats(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get statistics about the vector store
    
    Returns information about the number of documents, embedding model, and source distribution.
    """
    try:
        vs = get_vector_store()
        stats = vs.get_stats()
        
        return VectorStoreStatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stats: {str(e)}"
        )
