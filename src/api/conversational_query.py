"""
Conversational Query Lambda Handler

Handles POST /ask endpoint for RAG-based conversational queries
"""

import json
import os
from typing import Dict, Any

from src.services.rag_engine import RAGEngine, ConversationContext
from src.services.conversation_manager import ConversationManager
from src.utils.auth_middleware import extract_user_id


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle conversational query with RAG
    
    Request body:
    {
        "query": "What schemes are available for farmers?",
        "session_id": "optional-session-id",
        "language": "hi"
    }
    
    Response:
    {
        "answer": "Generated response",
        "sources": [{"scheme_id": "...", "name": "...", "relevance_score": 0.95}],
        "confidence": 0.92,
        "session_id": "session-id"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '').strip()
        session_id = body.get('session_id')
        language = body.get('language', 'hi')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'INVALID_REQUEST',
                    'message': 'Query is required'
                })
            }
        
        # Extract user ID from JWT token
        user_id = extract_user_id(event)
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'UNAUTHORIZED',
                    'message': 'Valid authentication required'
                })
            }
        
        # Initialize services
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        bedrock_model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-instant-v1')
        embedding_model_id = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
        
        rag_engine = RAGEngine(opensearch_endpoint, bedrock_model_id, embedding_model_id)
        conversation_manager = ConversationManager()
        
        # Get or create conversation context
        if session_id:
            conv_context = conversation_manager.get_context(session_id)
            if not conv_context:
                # Session expired or invalid, create new one
                session_id = conversation_manager.create_session(user_id, language)
                conv_context = conversation_manager.get_context(session_id)
        else:
            # Create new session
            session_id = conversation_manager.create_session(user_id, language)
            conv_context = conversation_manager.get_context(session_id)
        
        if not conv_context:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'SESSION_ERROR',
                    'message': 'Failed to create or retrieve session'
                })
            }
        
        # Process query with RAG
        rag_response = rag_engine.query(query, conv_context, top_k=5)
        
        # Update conversation context
        conversation_manager.add_turn(
            session_id=session_id,
            user_message=query,
            assistant_message=rag_response.answer
        )
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'answer': rag_response.answer,
                'sources': rag_response.sources,
                'confidence': rag_response.confidence,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        print(f"Error processing conversational query: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'INTERNAL_ERROR',
                'message': f'Failed to process query: {str(e)}'
            })
        }
