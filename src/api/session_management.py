"""
Session Management Lambda Handler

Handles session creation and deletion for conversational AI
"""

import json
from typing import Dict, Any

from src.services.conversation_manager import ConversationManager
from src.utils.auth_middleware import extract_user_id


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle session management operations
    
    POST /session/create:
    Request body:
    {
        "language": "hi"
    }
    Response:
    {
        "session_id": "uuid",
        "user_id": "user-id",
        "language": "hi",
        "created_at": "2024-01-20T10:00:00"
    }
    
    DELETE /session/{session_id}:
    Response:
    {
        "status": "deleted",
        "session_id": "uuid"
    }
    """
    try:
        http_method = event.get('httpMethod')
        path_parameters = event.get('pathParameters', {})
        
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
        
        conversation_manager = ConversationManager()
        
        if http_method == 'POST':
            # Create new session
            body = json.loads(event.get('body', '{}'))
            language = body.get('language', 'hi')
            
            session_id = conversation_manager.create_session(user_id, language)
            context = conversation_manager.get_context(session_id)
            
            if not context:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'SESSION_CREATION_FAILED',
                        'message': 'Failed to create session'
                    })
                }
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'session_id': context.session_id,
                    'user_id': context.user_id,
                    'language': context.language,
                    'created_at': context.created_at.isoformat()
                })
            }
        
        elif http_method == 'DELETE':
            # Delete session
            session_id = path_parameters.get('session_id')
            
            if not session_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'INVALID_REQUEST',
                        'message': 'Session ID is required'
                    })
                }
            
            # Verify session belongs to user
            context = conversation_manager.get_context(session_id)
            if context and context.user_id != user_id:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'FORBIDDEN',
                        'message': 'Cannot delete session belonging to another user'
                    })
                }
            
            success = conversation_manager.clear_session(session_id)
            
            if success:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'status': 'deleted',
                        'session_id': session_id
                    })
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'SESSION_NOT_FOUND',
                        'message': 'Session not found or already deleted'
                    })
                }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'METHOD_NOT_ALLOWED',
                    'message': f'Method {http_method} not allowed'
                })
            }
        
    except Exception as e:
        print(f"Error in session management: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'INTERNAL_ERROR',
                'message': f'Failed to manage session: {str(e)}'
            })
        }
