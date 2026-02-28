"""Impact tracking schemas for request/response validation"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class InteractionEventType(str, Enum):
    """Valid interaction event types"""
    QUERY_SUBMITTED = "query_submitted"
    SCHEME_ACCESSED = "scheme_accessed"
    JOB_DISCOVERED = "job_discovered"
    FACILITY_LOCATED = "facility_located"
    VOICE_INTERACTION = "voice_interaction"
    LANGUAGE_USED = "language_used"
    CROP_ADVICE_REQUESTED = "crop_advice_requested"
    FERTILIZER_ADVICE_REQUESTED = "fertilizer_advice_requested"
    MARKET_PRICE_CHECKED = "market_price_checked"
    SKILL_PROGRAM_VIEWED = "skill_program_viewed"
    HEALTH_CHECK_PERFORMED = "health_check_performed"


class OutcomeEventType(str, Enum):
    """Valid outcome event types"""
    SCHEME_APPLIED = "scheme_applied"
    JOB_APPLIED = "job_applied"
    FACILITY_VISITED = "facility_visited"
    SKILL_ENROLLED = "skill_enrolled"
    RECOMMENDATION_FOLLOWED = "recommendation_followed"
    CROP_PLANTED = "crop_planted"
    FERTILIZER_PURCHASED = "fertilizer_purchased"


class InteractionEventCreate(BaseModel):
    """Schema for creating an interaction event"""
    user_id: Optional[str] = Field(None, description="User ID (optional for anonymous tracking)")
    event_type: InteractionEventType = Field(..., description="Type of interaction event")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    language: Optional[str] = Field(None, pattern=r'^[a-z]{2}$', description="Language code")


class InteractionEventResponse(BaseModel):
    """Schema for interaction event response"""
    interaction_id: str
    user_id: Optional[str]
    event_type: str
    event_data: Optional[Dict[str, Any]]
    language: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class OutcomeEventCreate(BaseModel):
    """Schema for creating an outcome event"""
    user_id: Optional[str] = Field(None, description="User ID (optional for anonymous tracking)")
    outcome_type: OutcomeEventType = Field(..., description="Type of outcome event")
    outcome_data: Optional[Dict[str, Any]] = Field(None, description="Additional outcome data")


class OutcomeEventResponse(BaseModel):
    """Schema for outcome event response"""
    outcome_id: str
    user_id: Optional[str]
    outcome_type: str
    outcome_data: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricFilters(BaseModel):
    """Filters for impact metrics queries"""
    start_date: Optional[datetime] = Field(None, description="Start date for metrics")
    end_date: Optional[datetime] = Field(None, description="End date for metrics")
    region: Optional[str] = Field(None, description="Filter by state or district")
    language: Optional[str] = Field(None, description="Filter by language")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    outcome_type: Optional[str] = Field(None, description="Filter by outcome type")
    service_category: Optional[str] = Field(None, description="Filter by service category (schemes, farmer, skills, health)")


class ImpactMetrics(BaseModel):
    """Aggregated impact metrics"""
    users_served: int = Field(..., description="Total unique users served")
    queries_resolved: int = Field(..., description="Total queries resolved")
    schemes_accessed: int = Field(..., description="Number of scheme accesses")
    farmers_assisted: int = Field(..., description="Number of farmers assisted")
    jobs_discovered: int = Field(..., description="Number of jobs discovered")
    health_checks_performed: int = Field(..., description="Number of health checks")
    languages_used: Dict[str, int] = Field(..., description="Count by language")
    events_by_type: Dict[str, int] = Field(..., description="Count by event type")
    outcomes_by_type: Dict[str, int] = Field(..., description="Count by outcome type")
    success_rate: float = Field(..., description="Ratio of outcomes to interactions")
    period_start: datetime = Field(..., description="Start of metrics period")
    period_end: datetime = Field(..., description="End of metrics period")


class DateRange(BaseModel):
    """Date range for reports"""
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")


class ReportType(str, Enum):
    """Valid report types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class ImpactReport(BaseModel):
    """Impact report response"""
    report_type: str
    date_range: DateRange
    metrics: ImpactMetrics
    regional_breakdown: Dict[str, Dict[str, int]] = Field(..., description="Metrics by region")
    language_breakdown: Dict[str, Dict[str, int]] = Field(..., description="Metrics by language")
    service_breakdown: Dict[str, Dict[str, int]] = Field(..., description="Metrics by service category")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EventRecordResponse(BaseModel):
    """Response after recording an event"""
    success: bool
    event_id: str
    message: str = "Event recorded successfully"


class EventRequest(BaseModel):
    """Unified schema for event recording - supports both interaction and outcome events"""
    event: Optional[InteractionEventCreate] = Field(None, description="Interaction event data")
    outcome: Optional[OutcomeEventCreate] = Field(None, description="Outcome event data")
    
    @field_validator('event', 'outcome')
    @classmethod
    def check_at_least_one(cls, v, info):
        """Ensure at least one of event or outcome is provided"""
        # This will be checked in the endpoint logic
        return v
