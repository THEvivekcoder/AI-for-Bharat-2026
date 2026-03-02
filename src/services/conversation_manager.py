"""
Conversation Manager Service

Manages conversation sessions and context persistence using DynamoDB
"""

import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key

from src.services.rag_engine import ConversationContext, ConversationTurn


class ConversationManager:
    """Manages conversation sessions and persistence"""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize conversation manager
        
        Args:
            table_name: DynamoDB table name for sessions
        """
        self.table_name = table_name or os.environ.get('CONVERSATION_SESSIONS_TABLE')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_session(self, user_id: str, language: str = "hi") -> str:
        """
        Create new conversation session
        
        Args:
            user_id: User identifier
            language: Preferred language
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # TTL: 24 hours from now
        ttl = int((now + timedelta(hours=24)).timestamp())
        
        item = {
            'session_id': session_id,
            'user_id': user_id,
            'language': language,
            'history': [],
            'current_topic': None,
            'created_at': now.isoformat(),
            'last_activity': now.isoformat(),
            'ttl': ttl
        }
        
        self.table.put_item(Item=item)
        return session_id
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext or None if not found
        """
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Reconstruct conversation turns
            history = []
            for turn_data in item.get('history', []):
                turn = ConversationTurn(
                    user_message=turn_data['user_message'],
                    assistant_message=turn_data['assistant_message'],
                    timestamp=datetime.fromisoformat(turn_data['timestamp']),
                    intent=turn_data.get('intent'),
                    entities=turn_data.get('entities', {})
                )
                history.append(turn)
            
            context = ConversationContext(
                session_id=item['session_id'],
                user_id=item['user_id'],
                language=item['language'],
                history=history,
                current_topic=item.get('current_topic'),
                created_at=datetime.fromisoformat(item['created_at']),
                last_activity=datetime.fromisoformat(item['last_activity'])
            )
            
            return context
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return None
    
    def add_turn(self, session_id: str, user_message: str, 
                 assistant_message: str, intent: Optional[str] = None,
                 entities: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add conversation turn to session history
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response
            intent: Detected intent (optional)
            entities: Extracted entities (optional)
            
        Returns:
            True if successful
        """
        now = datetime.utcnow()
        
        turn_data = {
            'user_message': user_message,
            'assistant_message': assistant_message,
            'timestamp': now.isoformat(),
            'intent': intent,
            'entities': entities or {}
        }
        
        try:
            # Update TTL to extend session
            ttl = int((now + timedelta(hours=24)).timestamp())
            
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET history = list_append(if_not_exists(history, :empty_list), :turn), last_activity = :now, #ttl = :ttl',
                ExpressionAttributeNames={
                    '#ttl': 'ttl'
                },
                ExpressionAttributeValues={
                    ':turn': [turn_data],
                    ':now': now.isoformat(),
                    ':ttl': ttl,
                    ':empty_list': []
                }
            )
            return True
        except Exception as e:
            print(f"Error adding turn: {e}")
            return False
    
    def update_topic(self, session_id: str, topic: str) -> bool:
        """
        Update current conversation topic
        
        Args:
            session_id: Session identifier
            topic: Current topic
            
        Returns:
            True if successful
        """
        try:
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET current_topic = :topic',
                ExpressionAttributeValues={
                    ':topic': topic
                }
            )
            return True
        except Exception as e:
            print(f"Error updating topic: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history (delete session)
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            self.table.delete_item(Key={'session_id': session_id})
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> list:
        """
        Get recent sessions for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        try:
            response = self.table.query(
                IndexName='user-id-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            sessions = []
            for item in response.get('Items', []):
                sessions.append({
                    'session_id': item['session_id'],
                    'language': item['language'],
                    'created_at': item['created_at'],
                    'last_activity': item['last_activity'],
                    'turn_count': len(item.get('history', [])),
                    'current_topic': item.get('current_topic')
                })
            
            return sessions
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return []
