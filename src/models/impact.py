"""Impact tracking data models for BharatSahayak."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class InteractionEvent(BaseModel):
    """User interaction event for impact tracking."""
    
    event_id: Optional[str] = Field(None, description="Unique event identifier (auto-generated)")
    user_id: str = Field(..., min_length=1, description="User identifier")
    event_type: str = Field(
        ...,
        description="Event type: query_submitted, scheme_accessed, scheme_applied, job_discovered, facility_located, voice_interaction, language_used"
    )
    event_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible metadata storage for event-specific data"
    )
    language: Optional[str] = Field(None, description="Language used during interaction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type."""
        valid_types = [
            "query_submitted",
            "scheme_accessed",
            "scheme_applied",
            "job_discovered",
            "facility_located",
            "voice_interaction",
            "language_used"
        ]
        if v not in valid_types:
            raise ValueError(f"Event type must be one of: {', '.join(valid_types)}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "evt_123456",
                    "user_id": "user_123456",
                    "event_type": "query_submitted",
                    "event_data": {
                        "query": "What schemes are available for farmers?",
                        "category": "agriculture",
                        "response_time_ms": 1250
                    },
                    "language": "hi",
                    "timestamp": "2024-01-20T10:30:00Z"
                },
                {
                    "event_id": "evt_123457",
                    "user_id": "user_123456",
                    "event_type": "scheme_accessed",
                    "event_data": {
                        "scheme_id": "PM-KISAN-2024",
                        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
                        "category": "agriculture"
                    },
                    "language": "hi",
                    "timestamp": "2024-01-20T10:31:00Z"
                }
            ]
        }
    }


class OutcomeEvent(BaseModel):
    """Successful outcome event for impact tracking."""
    
    outcome_id: Optional[str] = Field(None, description="Unique outcome identifier (auto-generated)")
    user_id: str = Field(..., min_length=1, description="User identifier")
    outcome_type: str = Field(
        ...,
        description="Outcome type: scheme_applied, job_applied, facility_visited, skill_enrolled, recommendation_followed"
    )
    outcome_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible metadata storage for outcome-specific data"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Outcome timestamp")
    
    @field_validator("outcome_type")
    @classmethod
    def validate_outcome_type(cls, v: str) -> str:
        """Validate outcome type."""
        valid_types = [
            "scheme_applied",
            "job_applied",
            "facility_visited",
            "skill_enrolled",
            "recommendation_followed"
        ]
        if v not in valid_types:
            raise ValueError(f"Outcome type must be one of: {', '.join(valid_types)}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "outcome_id": "out_123456",
                    "user_id": "user_123456",
                    "outcome_type": "scheme_applied",
                    "outcome_data": {
                        "scheme_id": "PM-KISAN-2024",
                        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
                        "application_method": "online",
                        "success": True
                    },
                    "timestamp": "2024-01-20T11:00:00Z"
                },
                {
                    "outcome_id": "out_123457",
                    "user_id": "user_789012",
                    "outcome_type": "job_applied",
                    "outcome_data": {
                        "job_id": "job_456",
                        "job_title": "Village Health Worker",
                        "department": "Health Department"
                    },
                    "timestamp": "2024-01-20T14:30:00Z"
                }
            ]
        }
    }
