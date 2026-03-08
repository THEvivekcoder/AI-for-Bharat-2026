"""Lambda handler for recording impact tracking events."""

import json
import os
import logging
from typing import Dict, Any
from datetime import datetime

from src.core.impact_repository import ImpactRepository, DynamoDBRepositoryError
from src.models.impact import InteractionEvent, OutcomeEvent
from pydantic import ValidationError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
INTERACTIONS_TABLE = os.environ.get('INTERACTIONS_TABLE', 'bharatsahayak-interactions-dev')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
impact_repo = ImpactRepository(table_name=INTERACTIONS_TABLE, region_name=AWS_REGION)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /impact/event requests to record interaction or outcome events.
    
    Request Body:
    {
        "record_type": "interaction" | "outcome",
        "user_id": "user_123456",
        "event_type": "query_submitted" | "scheme_accessed" | ...,  // for interactions
        "outcome_type": "scheme_applied" | "job_applied" | ...,      // for outcomes
        "event_data": {
            // Flexible metadata
        },
        "outcome_data": {
            // Flexible metadata for outcomes
        },
        "language": "hi"  // Optional, for interactions
    }
    
    Response:
    {
        "event_id": "evt_123456" | "out_123456",
        "message": "Event recorded successfully"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        record_type = body.get('record_type')
        if not record_type:
            return error_response(400, "Missing required field: record_type")
        
        if record_type not in ['interaction', 'outcome']:
            return error_response(400, "record_type must be 'interaction' or 'outcome'")
        
        user_id = body.get('user_id')
        if not user_id:
            return error_response(400, "Missing required field: user_id")
        
        # Record interaction event
        if record_type == 'interaction':
            event_type = body.get('event_type')
            if not event_type:
                return error_response(400, "Missing required field: event_type for interaction")
            
            # Create InteractionEvent
            interaction = InteractionEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=body.get('event_data', {}),
                language=body.get('language'),
                timestamp=datetime.utcnow()
            )
            
            # Record in DynamoDB
            event_id = impact_repo.record_interaction(interaction)
            
            logger.info(f"Recorded interaction event {event_id} for user {user_id}")
            
            return success_response({
                'event_id': event_id,
                'message': 'Interaction event recorded successfully'
            }, status_code=201)
        
        # Record outcome event
        elif record_type == 'outcome':
            outcome_type = body.get('outcome_type')
            if not outcome_type:
                return error_response(400, "Missing required field: outcome_type for outcome")
            
            # Create OutcomeEvent
            outcome = OutcomeEvent(
                user_id=user_id,
                outcome_type=outcome_type,
                outcome_data=body.get('outcome_data', {}),
                timestamp=datetime.utcnow()
            )
            
            # Record in DynamoDB
            outcome_id = impact_repo.record_outcome(outcome)
            
            logger.info(f"Recorded outcome event {outcome_id} for user {user_id}")
            
            return success_response({
                'event_id': outcome_id,
                'message': 'Outcome event recorded successfully'
            }, status_code=201)
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, f"Invalid event data: {str(e)}")
    
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to record event")
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return error_response(400, "Invalid JSON in request body")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
