"""Impact tracking service for analytics and social impact measurement"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import logging

from app.models.impact import InteractionEvent, OutcomeEvent
from app.schemas.impact import (
    InteractionEventCreate,
    OutcomeEventCreate,
    MetricFilters,
    ImpactMetrics,
    DateRange,
    ImpactReport,
    ReportType
)

logger = logging.getLogger(__name__)


class ImpactTracker:
    """Service for tracking user interactions and measuring social impact"""
    
    def __init__(self, db: Session):
        """Initialize Impact Tracker with database session"""
        self.db = db
    
    def record_interaction(self, event: InteractionEventCreate) -> InteractionEvent:
        """
        Record user interaction event
        
        Args:
            event: Interaction event data
            
        Returns:
            Created InteractionEvent
            
        Events tracked:
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
        """
        try:
            # Convert user_id string to UUID if provided
            user_uuid = None
            if event.user_id:
                try:
                    user_uuid = UUID(event.user_id)
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid user_id format: {event.user_id}")
            
            # Create interaction event
            interaction = InteractionEvent(
                user_id=user_uuid,
                event_type=event.event_type.value,
                event_data=event.event_data,
                language=event.language,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            
            logger.info(f"Recorded interaction: {event.event_type.value} for user {event.user_id}")
            return interaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording interaction: {str(e)}")
            raise
    
    def record_outcome(self, outcome: OutcomeEventCreate) -> OutcomeEvent:
        """
        Record successful outcome event
        
        Args:
            outcome: Outcome event data
            
        Returns:
            Created OutcomeEvent
            
        Outcomes tracked:
        - scheme_applied: User applied for a scheme
        - job_applied: User applied for a job
        - facility_visited: User visited a health facility
        - skill_enrolled: User enrolled in skill program
        - recommendation_followed: User followed a recommendation
        - crop_planted: Farmer planted recommended crop
        - fertilizer_purchased: Farmer purchased recommended fertilizer
        """
        try:
            # Convert user_id string to UUID if provided
            user_uuid = None
            if outcome.user_id:
                try:
                    user_uuid = UUID(outcome.user_id)
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid user_id format: {outcome.user_id}")
            
            # Create outcome event
            outcome_event = OutcomeEvent(
                user_id=user_uuid,
                outcome_type=outcome.outcome_type.value,
                outcome_data=outcome.outcome_data,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(outcome_event)
            self.db.commit()
            self.db.refresh(outcome_event)
            
            logger.info(f"Recorded outcome: {outcome.outcome_type.value} for user {outcome.user_id}")
            return outcome_event
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording outcome: {str(e)}")
            raise
    
    def get_metrics(self, filters: MetricFilters) -> ImpactMetrics:
        """
        Get aggregated impact metrics with optional filters
        
        Args:
            filters: Filters for date range, region, language, etc.
            
        Returns:
            ImpactMetrics with aggregated data
            
        Metrics include:
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
            # Set default date range if not provided
            end_date = filters.end_date or datetime.utcnow()
            start_date = filters.start_date or (end_date - timedelta(days=30))
            
            # Build base query filters
            interaction_filters = [
                InteractionEvent.timestamp >= start_date,
                InteractionEvent.timestamp <= end_date
            ]
            outcome_filters = [
                OutcomeEvent.timestamp >= start_date,
                OutcomeEvent.timestamp <= end_date
            ]
            
            # Apply optional filters
            if filters.language:
                interaction_filters.append(InteractionEvent.language == filters.language)
            
            if filters.event_type:
                interaction_filters.append(InteractionEvent.event_type == filters.event_type)
            
            if filters.outcome_type:
                outcome_filters.append(OutcomeEvent.outcome_type == filters.outcome_type)
            
            # Apply region filter (check event_data JSONB)
            if filters.region:
                interaction_filters.append(
                    or_(
                        InteractionEvent.event_data['region'].astext == filters.region,
                        InteractionEvent.event_data['state'].astext == filters.region,
                        InteractionEvent.event_data['district'].astext == filters.region
                    )
                )
                outcome_filters.append(
                    or_(
                        OutcomeEvent.outcome_data['region'].astext == filters.region,
                        OutcomeEvent.outcome_data['state'].astext == filters.region,
                        OutcomeEvent.outcome_data['district'].astext == filters.region
                    )
                )
            
            # Apply service category filter
            if filters.service_category:
                category_events = self._get_events_for_category(filters.service_category)
                interaction_filters.append(InteractionEvent.event_type.in_(category_events))
            
            # Count unique users served
            users_served = self.db.query(
                func.count(func.distinct(InteractionEvent.user_id))
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.user_id.isnot(None)
            ).scalar() or 0
            
            # Count total queries resolved
            queries_resolved = self.db.query(
                func.count(InteractionEvent.interaction_id)
            ).filter(and_(*interaction_filters)).scalar() or 0
            
            # Count schemes accessed
            schemes_accessed = self.db.query(
                func.count(InteractionEvent.interaction_id)
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.event_type == 'scheme_accessed'
            ).scalar() or 0
            
            # Count farmers assisted (crop, fertilizer, or market price events)
            farmers_assisted = self.db.query(
                func.count(func.distinct(InteractionEvent.user_id))
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.event_type.in_([
                    'crop_advice_requested',
                    'fertilizer_advice_requested',
                    'market_price_checked'
                ]),
                InteractionEvent.user_id.isnot(None)
            ).scalar() or 0
            
            # Count jobs discovered
            jobs_discovered = self.db.query(
                func.count(InteractionEvent.interaction_id)
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.event_type == 'job_discovered'
            ).scalar() or 0
            
            # Count health checks performed
            health_checks = self.db.query(
                func.count(InteractionEvent.interaction_id)
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.event_type == 'health_check_performed'
            ).scalar() or 0
            
            # Get language breakdown
            languages_used = {}
            language_results = self.db.query(
                InteractionEvent.language,
                func.count(InteractionEvent.interaction_id)
            ).filter(
                and_(*interaction_filters),
                InteractionEvent.language.isnot(None)
            ).group_by(InteractionEvent.language).all()
            
            for lang, count in language_results:
                languages_used[lang] = count
            
            # Get events by type
            events_by_type = {}
            event_type_results = self.db.query(
                InteractionEvent.event_type,
                func.count(InteractionEvent.interaction_id)
            ).filter(and_(*interaction_filters)).group_by(
                InteractionEvent.event_type
            ).all()
            
            for event_type, count in event_type_results:
                events_by_type[event_type] = count
            
            # Get outcomes by type
            outcomes_by_type = {}
            outcome_type_results = self.db.query(
                OutcomeEvent.outcome_type,
                func.count(OutcomeEvent.outcome_id)
            ).filter(and_(*outcome_filters)).group_by(
                OutcomeEvent.outcome_type
            ).all()
            
            for outcome_type, count in outcome_type_results:
                outcomes_by_type[outcome_type] = count
            
            # Calculate success rate
            total_outcomes = sum(outcomes_by_type.values())
            success_rate = (total_outcomes / queries_resolved) if queries_resolved > 0 else 0.0
            
            return ImpactMetrics(
                users_served=users_served,
                queries_resolved=queries_resolved,
                schemes_accessed=schemes_accessed,
                farmers_assisted=farmers_assisted,
                jobs_discovered=jobs_discovered,
                health_checks_performed=health_checks,
                languages_used=languages_used,
                events_by_type=events_by_type,
                outcomes_by_type=outcomes_by_type,
                success_rate=round(success_rate, 4),
                period_start=start_date,
                period_end=end_date
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise
    
    def generate_report(self, report_type: ReportType, date_range: Optional[DateRange] = None) -> ImpactReport:
        """
        Generate comprehensive impact report for specified period
        
        Args:
            report_type: Type of report (daily, weekly, monthly, quarterly, custom)
            date_range: Optional custom date range (required for custom report type)
            
        Returns:
            ImpactReport with metrics and breakdowns
        """
        try:
            # Determine date range based on report type
            end_date = datetime.utcnow()
            
            if report_type == ReportType.DAILY:
                start_date = end_date - timedelta(days=1)
            elif report_type == ReportType.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif report_type == ReportType.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif report_type == ReportType.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            elif report_type == ReportType.CUSTOM:
                if not date_range:
                    raise ValueError("date_range required for custom report type")
                start_date = date_range.start_date
                end_date = date_range.end_date
            else:
                raise ValueError(f"Invalid report type: {report_type}")
            
            # Create date range
            report_date_range = DateRange(start_date=start_date, end_date=end_date)
            
            # Get overall metrics
            filters = MetricFilters(start_date=start_date, end_date=end_date)
            overall_metrics = self.get_metrics(filters)
            
            # Get regional breakdown
            regional_breakdown = self._get_regional_breakdown(start_date, end_date)
            
            # Get language breakdown
            language_breakdown = self._get_language_breakdown(start_date, end_date)
            
            # Get service breakdown
            service_breakdown = self._get_service_breakdown(start_date, end_date)
            
            return ImpactReport(
                report_type=report_type.value,
                date_range=report_date_range,
                metrics=overall_metrics,
                regional_breakdown=regional_breakdown,
                language_breakdown=language_breakdown,
                service_breakdown=service_breakdown,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _get_events_for_category(self, category: str) -> List[str]:
        """Get event types for a service category"""
        category_mapping = {
            'schemes': ['scheme_accessed'],
            'farmer': ['crop_advice_requested', 'fertilizer_advice_requested', 'market_price_checked'],
            'skills': ['skill_program_viewed', 'job_discovered'],
            'health': ['health_check_performed', 'facility_located']
        }
        return category_mapping.get(category, [])
    
    def _get_regional_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, int]]:
        """Get metrics breakdown by region"""
        regional_data = {}
        
        # Query interactions with region data
        results = self.db.query(
            InteractionEvent.event_data['state'].astext.label('state'),
            InteractionEvent.event_type,
            func.count(InteractionEvent.interaction_id)
        ).filter(
            InteractionEvent.timestamp >= start_date,
            InteractionEvent.timestamp <= end_date,
            InteractionEvent.event_data['state'].astext.isnot(None)
        ).group_by(
            InteractionEvent.event_data['state'].astext,
            InteractionEvent.event_type
        ).all()
        
        for state, event_type, count in results:
            if state not in regional_data:
                regional_data[state] = {}
            regional_data[state][event_type] = count
        
        return regional_data
    
    def _get_language_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, int]]:
        """Get metrics breakdown by language"""
        language_data = {}
        
        results = self.db.query(
            InteractionEvent.language,
            InteractionEvent.event_type,
            func.count(InteractionEvent.interaction_id)
        ).filter(
            InteractionEvent.timestamp >= start_date,
            InteractionEvent.timestamp <= end_date,
            InteractionEvent.language.isnot(None)
        ).group_by(
            InteractionEvent.language,
            InteractionEvent.event_type
        ).all()
        
        for language, event_type, count in results:
            if language not in language_data:
                language_data[language] = {}
            language_data[language][event_type] = count
        
        return language_data
    
    def _get_service_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, int]]:
        """Get metrics breakdown by service category"""
        service_data = {
            'schemes': {},
            'farmer': {},
            'skills': {},
            'health': {}
        }
        
        # Map event types to service categories
        event_to_service = {
            'scheme_accessed': 'schemes',
            'crop_advice_requested': 'farmer',
            'fertilizer_advice_requested': 'farmer',
            'market_price_checked': 'farmer',
            'skill_program_viewed': 'skills',
            'job_discovered': 'skills',
            'health_check_performed': 'health',
            'facility_located': 'health'
        }
        
        results = self.db.query(
            InteractionEvent.event_type,
            func.count(InteractionEvent.interaction_id)
        ).filter(
            InteractionEvent.timestamp >= start_date,
            InteractionEvent.timestamp <= end_date
        ).group_by(InteractionEvent.event_type).all()
        
        for event_type, count in results:
            service = event_to_service.get(event_type)
            if service:
                service_data[service][event_type] = count
        
        return service_data
