"""Impact tracking models for analytics and social impact measurement"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base


class InteractionEvent(Base):
    """User interaction events for impact tracking"""
    __tablename__ = "interactions"
    
    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    language = Column(String(10), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_interactions_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_interactions_event_type_timestamp', 'event_type', 'timestamp'),
    )


class OutcomeEvent(Base):
    """Successful outcome events for impact measurement"""
    __tablename__ = "outcomes"
    
    outcome_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    outcome_type = Column(String(50), nullable=False, index=True)
    outcome_data = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_outcomes_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_outcomes_outcome_type_timestamp', 'outcome_type', 'timestamp'),
    )
