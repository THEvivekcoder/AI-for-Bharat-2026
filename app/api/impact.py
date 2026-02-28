"""Impact tracking API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.services.impact_tracker import ImpactTracker
from app.schemas.impact import (
    InteractionEventCreate,
    InteractionEventResponse,
    OutcomeEventCreate,
    OutcomeEventResponse,
    MetricFilters,
    ImpactMetrics,
    ImpactReport,
    ReportType,
    DateRange,
    EventRecordResponse,
    EventRequest
)

router = APIRouter(prefix="/api/impact", tags=["impact"])


@router.post("/event", response_model=EventRecordResponse, status_code=status.HTTP_201_CREATED)
def record_event(
    request: EventRequest,
    db: Session = Depends(get_db)
):
    """
    Record an interaction or outcome event
    
    Provide either 'event' for interaction events or 'outcome' for outcome events.
    
    Interaction events tracked:
    - query_submitted: User submitted a query
    - scheme_accessed: User viewed scheme details
    - job_discovered: User found a job posting
    - facility_located: User found a health facility
    - voice_interaction: User used voice interface
    - language_used: User interacted in specific language
    - crop_advice_requested: Farmer requested crop advice
    - fertilizer_advice_requested: Farmer requested fertilizer guidance
    - market_price_checked: Farmer checked mandi prices
    - skill_program_viewed: User viewed skill program
    - health_check_performed: User performed health check
    
    Outcome events tracked:
    - scheme_applied: User applied for a scheme
    - job_applied: User applied for a job
    - facility_visited: User visited a health facility
    - skill_enrolled: User enrolled in skill program
    - recommendation_followed: User followed a recommendation
    - crop_planted: Farmer planted recommended crop
    - fertilizer_purchased: Farmer purchased recommended fertilizer
    """
    try:
        tracker = ImpactTracker(db)
        
        if request.event:
            # Record interaction event
            interaction = tracker.record_interaction(request.event)
            return EventRecordResponse(
                success=True,
                event_id=str(interaction.interaction_id),
                message="Interaction event recorded successfully"
            )
        elif request.outcome:
            # Record outcome event
            outcome_event = tracker.record_outcome(request.outcome)
            return EventRecordResponse(
                success=True,
                event_id=str(outcome_event.outcome_id),
                message="Outcome event recorded successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'event' or 'outcome' must be provided"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record event: {str(e)}"
        )


@router.get("", response_model=ImpactMetrics)
def get_impact_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    event_type: Optional[str] = None,
    outcome_type: Optional[str] = None,
    service_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get aggregated impact metrics with optional filters
    
    Query Parameters:
    - start_date: Start date for metrics (ISO format: YYYY-MM-DDTHH:MM:SS)
    - end_date: End date for metrics (ISO format: YYYY-MM-DDTHH:MM:SS)
    - region: Filter by state or district
    - language: Filter by language code
    - event_type: Filter by specific event type
    - outcome_type: Filter by specific outcome type
    - service_category: Filter by service (schemes, farmer, skills, health)
    
    Returns:
    - users_served: Total unique users
    - queries_resolved: Total queries
    - schemes_accessed: Scheme access count
    - farmers_assisted: Farmers who got advice
    - jobs_discovered: Jobs found
    - health_checks_performed: Health checks done
    - languages_used: Count by language
    - events_by_type: Count by event type
    - outcomes_by_type: Count by outcome type
    - success_rate: Ratio of outcomes to interactions
    """
    try:
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS): {str(e)}"
                )
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS): {str(e)}"
                )
        
        # Create filters
        filters = MetricFilters(
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            region=region,
            language=language,
            event_type=event_type,
            outcome_type=outcome_type,
            service_category=service_category
        )
        
        tracker = ImpactTracker(db)
        metrics = tracker.get_metrics(filters)
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/report", response_model=ImpactReport)
def generate_impact_report(
    report_type: str = "monthly",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive impact report
    
    Query Parameters:
    - report_type: Type of report (daily, weekly, monthly, quarterly, custom). Default: monthly
    - start_date: Start date for custom report (ISO format: YYYY-MM-DDTHH:MM:SS)
    - end_date: End date for custom report (ISO format: YYYY-MM-DDTHH:MM:SS)
    
    Report types:
    - daily: Last 24 hours
    - weekly: Last 7 days
    - monthly: Last 30 days
    - quarterly: Last 90 days
    - custom: Custom date range (requires start_date and end_date)
    
    Returns:
    - Overall metrics
    - Regional breakdown
    - Language breakdown
    - Service category breakdown
    """
    try:
        # Validate report type
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_type. Must be one of: daily, weekly, monthly, quarterly, custom"
            )
        
        tracker = ImpactTracker(db)
        
        # Parse custom date range if provided
        date_range = None
        if report_type_enum == ReportType.CUSTOM:
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date and end_date required for custom report"
                )
            
            try:
                date_range = DateRange(
                    start_date=datetime.fromisoformat(start_date),
                    end_date=datetime.fromisoformat(end_date)
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS): {str(e)}"
                )
        
        report = tracker.generate_report(report_type_enum, date_range)
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
