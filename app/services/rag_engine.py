"""
RAG (Retrieval-Augmented Generation) Engine for BharatSahayak
Handles query processing, context retrieval, and LLM-based response generation
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import os

from app.services.vector_store import VectorStore, Document, SearchResult

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    user_message: str
    assistant_message: str
    timestamp: datetime
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """Represents the context of a conversation session"""
    session_id: str
    user_id: str
    language: str
    history: List[ConversationTurn]
    user_profile: Optional[Dict[str, Any]] = None
    current_topic: Optional[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


@dataclass
class RAGResponse:
    """Response from RAG engine"""
    answer: str
    sources: List[SearchResult]
    confidence: float
    context_used: bool
    language: str
    metadata: Optional[Dict[str, Any]] = None


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine
    Combines semantic search with LLM for contextual responses
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize RAG engine
        
        Args:
            vector_store: Vector store for document retrieval
            llm_provider: LLM provider ('openai', 'local', etc.)
            llm_model: Model name
            api_key: API key for LLM provider
            temperature: LLM temperature for response generation
            max_tokens: Maximum tokens in response
        """
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM client
        if llm_provider == "openai":
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
            self.llm_client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        else:
            # Placeholder for other providers (local models, etc.)
            self.llm_client = None
    
    def query(
        self,
        user_query: str,
        context: Optional[ConversationContext] = None,
        top_k: int = 5,
        min_score: float = 0.7,
        prioritize_official: bool = True
    ) -> RAGResponse:
        """
        Process user query using RAG
        
        Args:
            user_query: User's question or query
            context: Conversation context for multi-turn conversations
            top_k: Number of documents to retrieve
            min_score: Minimum similarity score for retrieved documents
            prioritize_official: Whether to prioritize official sources
            
        Returns:
            RAGResponse with answer, sources, and metadata
        """
        # Step 1: Retrieve relevant documents
        source_filter = ['official', 'verified'] if prioritize_official else None
        search_results = self.vector_store.search(
            query=user_query,
            top_k=top_k,
            min_score=min_score,
            source_type_filter=source_filter
        )
        
        # If no results with filter, try without filter
        if not search_results and prioritize_official:
            search_results = self.vector_store.search(
                query=user_query,
                top_k=top_k,
                min_score=min_score,
                source_type_filter=None
            )
        
        # Step 2: Construct prompt with retrieved context
        prompt = self._construct_prompt(
            user_query=user_query,
            search_results=search_results,
            context=context
        )
        
        # Step 3: Generate response using LLM
        answer = self._generate_response(prompt, context)
        
        # Step 4: Calculate confidence based on retrieval scores
        confidence = self._calculate_confidence(search_results)
        
        # Determine language from context or default to English
        language = context.language if context else "en"
        
        return RAGResponse(
            answer=answer,
            sources=search_results,
            confidence=confidence,
            context_used=bool(search_results),
            language=language,
            metadata={
                "num_sources": len(search_results),
                "top_score": search_results[0].score if search_results else 0.0,
                "model": self.llm_model
            }
        )
    
    def _construct_prompt(
        self,
        user_query: str,
        search_results: List[SearchResult],
        context: Optional[ConversationContext] = None
    ) -> str:
        """
        Construct prompt for LLM with retrieved context
        
        Args:
            user_query: User's query
            search_results: Retrieved documents
            context: Conversation context
            
        Returns:
            Formatted prompt string
        """
        # System prompt
        system_prompt = """You are BharatSahayak, a helpful AI assistant designed to help rural and semi-urban Indians access government services, agricultural guidance, skill development, and healthcare information.

Your responses should be:
- Clear and simple, appropriate for users with varying literacy levels
- Based on the provided context documents
- Accurate and factual, citing official sources when available
- Helpful and actionable, providing step-by-step guidance when needed
- Respectful of cultural context and local practices

If you don't have enough information to answer confidently, say so and suggest alternatives."""
        
        # Add conversation history if available
        history_text = ""
        if context and context.history:
            history_text = "\n\nPrevious conversation:\n"
            for turn in context.history[-3:]:  # Last 3 turns for context
                history_text += f"User: {turn.user_message}\n"
                history_text += f"Assistant: {turn.assistant_message}\n"
        
        # Add retrieved context
        context_text = ""
        if search_results:
            context_text = "\n\nRelevant information from knowledge base:\n"
            for i, result in enumerate(search_results, 1):
                doc = result.document
                context_text += f"\n[Source {i}] ({doc.source_type}): {doc.content}\n"
                context_text += f"Source: {doc.source}\n"
        
        # Construct final prompt
        prompt = f"""{system_prompt}
{history_text}
{context_text}

User question: {user_query}

Please provide a helpful response based on the information above. If the information is from official sources, mention that. If you're uncertain, acknowledge it."""
        
        return prompt
    
    def _generate_response(
        self,
        prompt: str,
        context: Optional[ConversationContext] = None
    ) -> str:
        """
        Generate response using LLM
        
        Args:
            prompt: Formatted prompt
            context: Conversation context
            
        Returns:
            Generated response text
        """
        if self.llm_provider == "openai" and self.llm_client:
            try:
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                # Fallback response if LLM fails
                return f"I apologize, but I'm having trouble generating a response right now. Error: {str(e)}"
        else:
            # Fallback for when LLM is not available
            return "I apologize, but the AI response generation service is currently unavailable. Please try again later or contact support."
    
    def _calculate_confidence(self, search_results: List[SearchResult]) -> float:
        """
        Calculate confidence score based on retrieval results
        
        Args:
            search_results: Retrieved documents
            
        Returns:
            Confidence score between 0 and 1
        """
        if not search_results:
            return 0.0
        
        # Base confidence on top result score and number of results
        top_score = search_results[0].score
        num_results = len(search_results)
        
        # Higher confidence if:
        # - Top result has high similarity score
        # - Multiple relevant results found
        # - Results include official sources
        official_count = sum(1 for r in search_results if r.document.source_type == 'official')
        
        confidence = (
            top_score * 0.6 +  # Top result similarity
            min(num_results / 5, 1.0) * 0.2 +  # Number of results
            min(official_count / 3, 1.0) * 0.2  # Official sources
        )
        
        return min(confidence, 1.0)
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of documents to add
        """
        self.vector_store.add_documents(documents)
    
    def update_context(
        self,
        context: ConversationContext,
        user_query: str,
        response: str
    ) -> ConversationContext:
        """
        Update conversation context with new turn
        
        Args:
            context: Current conversation context
            user_query: User's query
            response: Assistant's response
            
        Returns:
            Updated conversation context
        """
        turn = ConversationTurn(
            user_message=user_query,
            assistant_message=response,
            timestamp=datetime.utcnow()
        )
        
        context.history.append(turn)
        context.last_activity = datetime.utcnow()
        
        return context
    
    def handle_out_of_scope(self, query: str) -> str:
        """
        Handle queries outside system's domain
        
        Args:
            query: User query
            
        Returns:
            Response indicating limitations
        """
        return """I apologize, but that question is outside my area of expertise. I'm designed to help with:

- Government schemes and benefits
- Agricultural guidance (crops, fertilizers, market prices)
- Skill development and employment opportunities
- Basic health information and facility locations

Please ask me about these topics, and I'll be happy to help!"""
    
    def detect_out_of_scope(self, query: str, search_results: List[SearchResult]) -> bool:
        """
        Detect if query is outside system's domain
        
        Args:
            query: User query
            search_results: Retrieved documents
            
        Returns:
            True if query appears out of scope
        """
        # Simple heuristic: if no good matches found, likely out of scope
        if not search_results:
            return True
        
        if search_results[0].score < 0.5:
            return True
        
        return False
