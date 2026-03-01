"""Repository for impact tracking events in DynamoDB."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
import logging

from .base_repository import BaseRepository, DynamoDBRepositoryError
from src.models.impact import InteractionEvent, OutcomeEvent

logger = logging.getLogger(__name__)


class ImpactRepository(BaseRepository):
    """Repository for storing and retrieving impact tracking events."""
    
    def __init__(self, table_name: str = "bharatsahayak-interactions-dev", region_name: str = "us-east-1"):
        """
        Initialize impact repository.
        
        Args:
            table_name: Name of the DynamoDB Interactions table
            region_name: AWS region name
        """
        super().__init__(table_name, region_name)
    
    def record_interaction(self, event: InteractionEvent) -> str:
        """
        Record an interaction event in DynamoDB.
        
        Args:
            event: InteractionEvent to record
            
        Returns:
            event_id: Generated event ID
            
        Raises:
            DynamoDBRepositoryError: If recording fails
        """
        try:
            # Generate event ID if not provided
            event_id = event.event_id or f"evt_{uuid.uuid4().hex[:12]}"
            
            # Prepare item for DynamoDB
            item = {
                'event_id': event_id,
                'user_id': event.user_id,
                'event_type': event.event_type,
                'event_data': event.event_data,
                'timestamp': event.timestamp.isoformat(),
                'record_type': 'interaction'  # Discriminator for queries
            }
            
            # Add optional language field
            if event.language:
                item['language'] = event.language
            
            # Store in DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Recorded interaction event: {event_id} for user {event.user_id}")
            return event_id
            
        except ClientError as e:
            self._handle_client_error(e, "record_interaction")
            raise
        except Exception as e:
            logger.error(f"Unexpected error recording interaction: {str(e)}")
            raise DynamoDBRepositoryError(f"Failed to record interaction: {str(e)}")
    
    def record_outcome(self, outcome: OutcomeEvent) -> str:
        """
        Record an outcome event in DynamoDB.
        
        Args:
            outcome: OutcomeEvent to record
            
        Returns:
            outcome_id: Generated outcome ID
            
        Raises:
            DynamoDBRepositoryError: If recording fails
        """
        try:
            # Generate outcome ID if not provided
            outcome_id = outcome.outcome_id or f"out_{uuid.uuid4().hex[:12]}"
            
            # Prepare item for DynamoDB
            item = {
                'event_id': outcome_id,  # Using event_id as partition key
                'user_id': outcome.user_id,
                'outcome_type': outcome.outcome_type,
                'outcome_data': outcome.outcome_data,
                'timestamp': outcome.timestamp.isoformat(),
                'record_type': 'outcome'  # Discriminator for queries
            }
            
            # Store in DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Recorded outcome event: {outcome_id} for user {outcome.user_id}")
            return outcome_id
            
        except ClientError as e:
            self._handle_client_error(e, "record_outcome")
            raise
        except Exception as e:
            logger.error(f"Unexpected error recording outcome: {str(e)}")
            raise DynamoDBRepositoryError(f"Failed to record outcome: {str(e)}")
    
    def get_user_interactions(
        self,
        user_id: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[InteractionEvent]:
        """
        Get interaction events for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of InteractionEvent objects
            
        Raises:
            DynamoDBRepositoryError: If query fails
        """
        try:
            # Query by user_id (requires GSI on user_id)
            # For now, we'll scan with filter (not optimal for production)
            filter_expression = "user_id = :user_id AND record_type = :record_type"
            expression_values = {
                ':user_id': user_id,
                ':record_type': 'interaction'
            }
            
            # Add date filters if provided
            if start_date:
                filter_expression += " AND #ts >= :start_date"
                expression_values[':start_date'] = start_date.isoformat()
            
            if end_date:
                filter_expression += " AND #ts <= :end_date"
                expression_values[':end_date'] = end_date.isoformat()
            
            # Scan with filter
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames={'#ts': 'timestamp'},
                Limit=limit
            )
            
            # Convert to InteractionEvent objects
            events = []
            for item in response.get('Items', []):
                events.append(InteractionEvent(
                    event_id=item['event_id'],
                    user_id=item['user_id'],
                    event_type=item['event_type'],
                    event_data=item.get('event_data', {}),
                    language=item.get('language'),
                    timestamp=datetime.fromisoformat(item['timestamp'])
                ))
            
            return events
            
        except ClientError as e:
            self._handle_client_error(e, "get_user_interactions")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user interactions: {str(e)}")
            raise DynamoDBRepositoryError(f"Failed to get user interactions: {str(e)}")
    
    def get_all_events(
        self,
        limit: int = 1000,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events (interactions and outcomes) for analytics.
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional filter by event_type or outcome_type
            
        Returns:
            List of event dictionaries
            
        Raises:
            DynamoDBRepositoryError: If scan fails
        """
        try:
            scan_kwargs = {'Limit': limit}
            
            # Add event type filter if provided
            if event_type:
                scan_kwargs['FilterExpression'] = "event_type = :event_type OR outcome_type = :event_type"
                scan_kwargs['ExpressionAttributeValues'] = {':event_type': event_type}
            
            # Scan table
            response = self.table.scan(**scan_kwargs)
            
            return response.get('Items', [])
            
        except ClientError as e:
            self._handle_client_error(e, "get_all_events")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting all events: {str(e)}")
            raise DynamoDBRepositoryError(f"Failed to get all events: {str(e)}")
    
    def get_analytics_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics data with filters.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            category: Optional category filter (from event_data)
            limit: Maximum number of events to scan
            
        Returns:
            Dictionary with aggregated metrics
            
        Raises:
            DynamoDBRepositoryError: If query fails
        """
        try:
            # Build filter expression
            filter_parts = []
            expression_values = {}
            expression_names = {}
            
            if start_date:
                filter_parts.append("#ts >= :start_date")
                expression_values[':start_date'] = start_date.isoformat()
                expression_names['#ts'] = 'timestamp'
            
            if end_date:
                filter_parts.append("#ts <= :end_date")
                expression_values[':end_date'] = end_date.isoformat()
                expression_names['#ts'] = 'timestamp'
            
            # Scan with filters
            scan_kwargs = {'Limit': limit}
            if filter_parts:
                scan_kwargs['FilterExpression'] = ' AND '.join(filter_parts)
                scan_kwargs['ExpressionAttributeValues'] = expression_values
                scan_kwargs['ExpressionAttributeNames'] = expression_names
            
            response = self.table.scan(**scan_kwargs)
            events = response.get('Items', [])
            
            # Aggregate metrics
            metrics = self._aggregate_metrics(events, category)
            
            return metrics
            
        except ClientError as e:
            self._handle_client_error(e, "get_analytics_data")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting analytics data: {str(e)}")
            raise DynamoDBRepositoryError(f"Failed to get analytics data: {str(e)}")
    
    def _aggregate_metrics(self, events: List[Dict[str, Any]], category_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregate events into metrics.
        
        Args:
            events: List of event dictionaries
            category_filter: Optional category filter
            
        Returns:
            Dictionary with aggregated metrics
        """
        # Initialize counters
        unique_users = set()
        total_queries = 0
        schemes_accessed = 0
        schemes_applied = 0
        jobs_discovered = 0
        facilities_located = 0
        
        # Counters by category
        category_counts = {}
        
        # Counters by language
        language_counts = {}
        
        # Process each event
        for event in events:
            record_type = event.get('record_type', 'interaction')
            user_id = event.get('user_id')
            
            # Track unique users (anonymized in final output)
            if user_id:
                unique_users.add(user_id)
            
            # Process interaction events
            if record_type == 'interaction':
                event_type = event.get('event_type')
                event_data = event.get('event_data', {})
                language = event.get('language')
                
                # Apply category filter if specified
                event_category = event_data.get('category')
                if category_filter and event_category != category_filter:
                    continue
                
                # Count by event type
                if event_type == 'query_submitted':
                    total_queries += 1
                elif event_type == 'scheme_accessed':
                    schemes_accessed += 1
                elif event_type == 'job_discovered':
                    jobs_discovered += 1
                elif event_type == 'facility_located':
                    facilities_located += 1
                
                # Count by category
                if event_category:
                    category_counts[event_category] = category_counts.get(event_category, 0) + 1
                
                # Count by language
                if language:
                    language_counts[language] = language_counts.get(language, 0) + 1
            
            # Process outcome events
            elif record_type == 'outcome':
                outcome_type = event.get('outcome_type')
                outcome_data = event.get('outcome_data', {})
                
                # Apply category filter if specified
                if category_filter:
                    # Check if outcome relates to the category
                    scheme_id = outcome_data.get('scheme_id')
                    if not scheme_id:
                        continue
                
                # Count by outcome type
                if outcome_type == 'scheme_applied':
                    schemes_applied += 1
        
        # Calculate success rate (schemes applied / schemes accessed)
        success_rate = 0.0
        if schemes_accessed > 0:
            success_rate = (schemes_applied / schemes_accessed) * 100
        
        # Build metrics dictionary (anonymized)
        metrics = {
            'total_users': len(unique_users),
            'total_queries': total_queries,
            'schemes_accessed': schemes_accessed,
            'schemes_applied': schemes_applied,
            'jobs_discovered': jobs_discovered,
            'facilities_located': facilities_located,
            'success_rate': round(success_rate, 2),
            'by_category': category_counts,
            'by_language': language_counts
        }
        
        return metrics
