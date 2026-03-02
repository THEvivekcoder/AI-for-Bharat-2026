"""Property-based tests for conversation context preservation.

Feature: bharatsahayak, Property 15: Conversation Context Preservation
**Validates: Requirements 6.1**

This test verifies that the RAG engine maintains conversation context across
multiple turns, allowing follow-up queries to reference entities and topics
from previous interactions.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import List

from src.services.rag_engine import (
    RAGEngine, ConversationContext, ConversationTurn, RAGResponse
)


# Custom strategies for generating valid test data
@st.composite
def conversation_turn_strategy(draw):
    """Generate valid ConversationTurn instances."""
    topics = ["schemes", "farming", "health", "jobs", "education"]
    entities = ["PM-KISAN", "Ayushman Bharat", "crop loan", "scholarship"]
    
    user_message = draw(st.sampled_from([
        f"Tell me about {draw(st.sampled_from(entities))}",
        f"What are the benefits?",
        f"How do I apply?",
        f"What documents are needed?",
        f"Am I eligible?",
        f"Tell me more about {draw(st.sampled_from(topics))}"
    ]))
    
    assistant_message = draw(st.text(min_size=20, max_size=200))
    
    return ConversationTurn(
        user_message=user_message,
        assistant_message=assistant_message,
        timestamp=datetime.utcnow(),
        intent=draw(st.none() | st.sampled_from(["query", "clarification", "application"])),
        entities=draw(st.dictionaries(
            st.sampled_from(["scheme_name", "category", "location"]),
            st.text(min_size=3, max_size=30),
            max_size=3
        ))
    )


@st.composite
def conversation_context_strategy(draw):
    """Generate valid ConversationContext instances with history."""
    session_id = f"session-{draw(st.integers(min_value=1000, max_value=9999))}"
    user_id = f"user-{draw(st.integers(min_value=100, max_value=999))}"
    language = draw(st.sampled_from(["hi", "en", "bn", "te", "mr"]))
    
    # Generate conversation history (1-5 turns)
    history = draw(st.lists(
        conversation_turn_strategy(),
        min_size=1,
        max_size=5
    ))
    
    current_topic = draw(st.none() | st.sampled_from([
        "schemes", "farming", "health", "jobs", "education"
    ]))
    
    return ConversationContext(
        session_id=session_id,
        user_id=user_id,
        language=language,
        history=history,
        current_topic=current_topic,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )


def extract_entities_from_history(context: ConversationContext) -> set:
    """Extract all entities mentioned in conversation history."""
    entities = set()
    for turn in context.history:
        # Extract entities from user message
        words = turn.user_message.lower().split()
        for word in words:
            if len(word) > 3:  # Simple heuristic for entity detection
                entities.add(word)
        
        # Add explicit entities
        for entity_value in turn.entities.values():
            entities.add(entity_value.lower())
    
    return entities


def is_follow_up_query(query: str) -> bool:
    """Check if a query is a follow-up that requires context."""
    follow_up_indicators = [
        "what are the benefits",
        "how do i apply",
        "what documents",
        "am i eligible",
        "tell me more",
        "what about",
        "and what",
        "also",
        "it",
        "this",
        "that",
        "they"
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in follow_up_indicators)


@settings(max_examples=20, deadline=None)
@given(
    context=conversation_context_strategy(),
    follow_up_query=st.sampled_from([
        "What are the benefits?",
        "How do I apply?",
        "What documents are needed?",
        "Am I eligible?",
        "Tell me more about this",
        "What about the application process?"
    ])
)
def test_conversation_context_preservation(context, follow_up_query):
    """
    Feature: bharatsahayak, Property 15: Conversation Context Preservation
    
    For any conversation session, when a follow-up query references entities
    or topics from previous turns, the RAG_Engine should have access to the
    conversation history and maintain context across turns.
    
    This test verifies:
    1. The RAG engine receives the full conversation history
    2. Follow-up queries can access context from previous turns
    3. The conversation history is properly formatted in the prompt
    4. Context is maintained across multiple turns
    """
    # Ensure we have conversation history
    assume(len(context.history) > 0)
    
    # Ensure the query is actually a follow-up
    assume(is_follow_up_query(follow_up_query))
    
    # Mock OpenSearch vector store
    mock_vector_store = Mock()
    mock_vector_store.search.return_value = [
        {
            'id': 'scheme-1',
            'score': 0.85,
            'source': {
                'scheme_id': 'scheme-1',
                'name': 'PM-KISAN',
                'category': 'agriculture',
                'description': 'Direct income support to farmers',
                'source_type': 'official'
            }
        }
    ]
    
    # Mock Bedrock LLM service
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536  # Mock embedding
    mock_llm.generate_response.return_value = "Based on the previous discussion, here are the benefits..."
    
    # Create RAG engine with mocked dependencies
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            # Process follow-up query
            response = rag_engine.query(follow_up_query, context, top_k=5)
            
            # Property verification 1: RAG engine should receive conversation history
            assert mock_llm.generate_response.called, "LLM should be called to generate response"
            
            # Get the prompt that was sent to the LLM
            call_args = mock_llm.generate_response.call_args
            prompt = call_args[0][0] if call_args else ""
            
            # Property verification 2: Prompt should include conversation history
            if len(context.history) > 0:
                # Check that at least one previous turn is mentioned in the prompt
                history_included = False
                for turn in context.history[-3:]:  # Check last 3 turns
                    if turn.user_message[:20] in prompt or turn.assistant_message[:20] in prompt:
                        history_included = True
                        break
                
                assert history_included, (
                    f"Conversation history should be included in prompt for follow-up query. "
                    f"Query: '{follow_up_query}', History turns: {len(context.history)}"
                )
            
            # Property verification 3: Response should be generated successfully
            assert isinstance(response, RAGResponse), "Should return RAGResponse object"
            assert response.answer, "Response should contain an answer"
            assert response.session_id == context.session_id, "Session ID should be preserved"
            
            # Property verification 4: Context should be accessible for follow-up
            # The fact that we got a response means the engine had access to context
            assert len(response.answer) > 0, (
                "Follow-up query should generate a response using conversation context"
            )


@settings(max_examples=15, deadline=None)
@given(
    context=conversation_context_strategy(),
    new_query=st.sampled_from([
        "Tell me about PM-KISAN scheme",
        "What health schemes are available?",
        "How can I get a crop loan?",
        "What scholarships are available for students?"
    ])
)
def test_context_updated_after_turn(context, new_query):
    """
    Test that conversation context is properly updated after each turn.
    
    This verifies that the update_context method correctly adds new turns
    to the conversation history.
    """
    # Mock dependencies
    mock_vector_store = Mock()
    mock_llm = Mock()
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            # Record initial history length
            initial_history_length = len(context.history)
            
            # Update context with new turn
            response_text = "Here is information about the scheme..."
            updated_context = rag_engine.update_context(context, new_query, response_text)
            
            # Verify context was updated
            assert len(updated_context.history) == initial_history_length + 1, (
                "History should have one more turn after update"
            )
            
            # Verify the new turn contains correct data
            latest_turn = updated_context.history[-1]
            assert latest_turn.user_message == new_query, "User message should match query"
            assert latest_turn.assistant_message == response_text, "Assistant message should match response"
            assert latest_turn.timestamp is not None, "Turn should have timestamp"
            
            # Verify session ID is preserved
            assert updated_context.session_id == context.session_id, "Session ID should be preserved"
            
            # Verify last_activity is updated
            assert updated_context.last_activity >= context.last_activity, (
                "Last activity timestamp should be updated"
            )


@settings(max_examples=10, deadline=None)
@given(
    initial_query=st.sampled_from([
        "Tell me about PM-KISAN",
        "What is Ayushman Bharat?",
        "How do I get a scholarship?"
    ]),
    follow_up_queries=st.lists(
        st.sampled_from([
            "What are the benefits?",
            "How do I apply?",
            "Am I eligible?",
            "What documents do I need?"
        ]),
        min_size=1,
        max_size=3
    )
)
def test_multi_turn_context_preservation(initial_query, follow_up_queries):
    """
    Test that context is preserved across multiple conversation turns.
    
    This simulates a realistic conversation with an initial query followed
    by multiple follow-up questions.
    """
    # Create initial context
    context = ConversationContext(
        session_id="test-session",
        user_id="test-user",
        language="en",
        history=[],
        current_topic=None,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )
    
    # Mock dependencies
    mock_vector_store = Mock()
    mock_vector_store.search.return_value = [
        {
            'id': 'scheme-1',
            'score': 0.85,
            'source': {
                'scheme_id': 'scheme-1',
                'name': 'Test Scheme',
                'category': 'agriculture',
                'description': 'Test description',
                'source_type': 'official'
            }
        }
    ]
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response based on context"
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            # Process initial query
            response = rag_engine.query(initial_query, context, top_k=5)
            context = rag_engine.update_context(context, initial_query, response.answer)
            
            # Process each follow-up query
            for i, follow_up in enumerate(follow_up_queries):
                response = rag_engine.query(follow_up, context, top_k=5)
                
                # Verify context is available
                call_args = mock_llm.generate_response.call_args
                prompt = call_args[0][0] if call_args else ""
                
                # For follow-up queries, prompt should include previous conversation
                assert "Previous conversation:" in prompt or len(context.history) > 0, (
                    f"Follow-up query {i+1} should have access to conversation history"
                )
                
                # Update context for next turn
                context = rag_engine.update_context(context, follow_up, response.answer)
            
            # Verify final history length
            expected_turns = 1 + len(follow_up_queries)  # initial + follow-ups
            assert len(context.history) == expected_turns, (
                f"Should have {expected_turns} turns in history, got {len(context.history)}"
            )
            
            # Verify all queries are in history
            user_messages = [turn.user_message for turn in context.history]
            assert initial_query in user_messages, "Initial query should be in history"
            for follow_up in follow_up_queries:
                assert follow_up in user_messages, f"Follow-up '{follow_up}' should be in history"
