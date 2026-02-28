"""
Conversation Manager for BharatSahayak
Handles session management and conversation context storage using Redis
"""

import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.rag_engine import ConversationContext, ConversationTurn
from app.redis_client import get_redis


class ConversationManager:
    """
    Manages conversation sessions and context
    Uses Redis for session storage with TTL
    """
    
    def __init__(self, session_ttl_hours: int = 24):
        """
        Initialize conversation manager
        
        Args:
            session_ttl_hours: Time-to-live for sessions in hours
        """
        self.redis_client = get_redis()
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.session_prefix = "conversation:session:"
    
    def create_session(
        self,
        user_id: str,
        language: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id: User identifier
            language: User's preferred language
            user_profile: Optional user profile data
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            language=language,
            history=[],
            user_profile=user_profile,
            current_topic=None,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        # Store in Redis
        self._save_context(context)
        
        return session_id
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext if found, None otherwise
        """
        key = f"{self.session_prefix}{session_id}"
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            
            # Deserialize from JSON
            context_dict = json.loads(data)
            context = self._dict_to_context(context_dict)
            
            return context
        except Exception as e:
            print(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_context(self, context: ConversationContext) -> bool:
        """
        Update conversation context in storage
        
        Args:
            context: Updated conversation context
            
        Returns:
            True if successful, False otherwise
        """
        context.last_activity = datetime.utcnow()
        return self._save_context(context)
    
    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a conversation turn to the session
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response
            intent: Detected intent (optional)
            entities: Extracted entities (optional)
            
        Returns:
            True if successful, False otherwise
        """
        context = self.get_context(session_id)
        if context is None:
            return False
        
        turn = ConversationTurn(
            user_message=user_message,
            assistant_message=assistant_message,
            timestamp=datetime.utcnow(),
            intent=intent,
            entities=entities
        )
        
        context.history.append(turn)
        
        return self.update_context(context)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        key = f"{self.session_prefix}{session_id}"
        
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Error clearing session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (alias for clear_session)
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.clear_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> list[str]:
        """
        Get all active session IDs for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session IDs
        """
        # Scan for all session keys
        pattern = f"{self.session_prefix}*"
        session_ids = []
        
        try:
            for key in self.redis_client.scan_iter(match=pattern):
                data = self.redis_client.get(key)
                if data:
                    context_dict = json.loads(data)
                    if context_dict.get("user_id") == user_id:
                        session_ids.append(context_dict.get("session_id"))
        except Exception as e:
            print(f"Error getting user sessions: {e}")
        
        return session_ids
    
    def extend_session(self, session_id: str) -> bool:
        """
        Extend the TTL of a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        key = f"{self.session_prefix}{session_id}"
        
        try:
            ttl_seconds = int(self.session_ttl.total_seconds())
            result = self.redis_client.expire(key, ttl_seconds)
            return result
        except Exception as e:
            print(f"Error extending session {session_id}: {e}")
            return False
    
    def _save_context(self, context: ConversationContext) -> bool:
        """
        Save conversation context to Redis
        
        Args:
            context: Conversation context to save
            
        Returns:
            True if successful, False otherwise
        """
        key = f"{self.session_prefix}{context.session_id}"
        
        try:
            # Serialize to JSON
            context_dict = self._context_to_dict(context)
            data = json.dumps(context_dict)
            
            # Store with TTL
            ttl_seconds = int(self.session_ttl.total_seconds())
            self.redis_client.setex(key, ttl_seconds, data)
            
            return True
        except Exception as e:
            print(f"Error saving context for session {context.session_id}: {e}")
            return False
    
    def _context_to_dict(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Convert ConversationContext to dictionary for JSON serialization
        
        Args:
            context: Conversation context
            
        Returns:
            Dictionary representation
        """
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "language": context.language,
            "history": [
                {
                    "user_message": turn.user_message,
                    "assistant_message": turn.assistant_message,
                    "timestamp": turn.timestamp.isoformat(),
                    "intent": turn.intent,
                    "entities": turn.entities
                }
                for turn in context.history
            ],
            "user_profile": context.user_profile,
            "current_topic": context.current_topic,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat()
        }
    
    def _dict_to_context(self, data: Dict[str, Any]) -> ConversationContext:
        """
        Convert dictionary to ConversationContext
        
        Args:
            data: Dictionary representation
            
        Returns:
            ConversationContext object
        """
        history = [
            ConversationTurn(
                user_message=turn["user_message"],
                assistant_message=turn["assistant_message"],
                timestamp=datetime.fromisoformat(turn["timestamp"]),
                intent=turn.get("intent"),
                entities=turn.get("entities")
            )
            for turn in data.get("history", [])
        ]
        
        return ConversationContext(
            session_id=data["session_id"],
            user_id=data["user_id"],
            language=data["language"],
            history=history,
            user_profile=data.get("user_profile"),
            current_topic=data.get("current_topic"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"])
        )
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session stats or None if not found
        """
        context = self.get_context(session_id)
        if context is None:
            return None
        
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "language": context.language,
            "num_turns": len(context.history),
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "duration_minutes": (context.last_activity - context.created_at).total_seconds() / 60,
            "current_topic": context.current_topic
        }
