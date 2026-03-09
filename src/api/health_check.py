"""Lambda handler for health check endpoint."""

import json
import os
import logging
from typing import Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
VERSION = os.environ.get('VERSION', '1.0.0')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle health check requests.
    
    GET /health-check
    
    Response:
    {
        "status": "healthy",
        "timestamp": "2024-01-20T10:00:00Z",
        "environment": "development",
        "version": "1.0.0",
        "region": "ap-south-1",
        "services": {
            "dynamodb": "healthy",
            "cognito": "healthy"
        }
    }
    """
    try:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Check service health
        services_health = check_services_health()
        
        # Determine overall status
        overall_status = "healthy"
        if any(status != "healthy" for status in services_health.values()):
            overall_status = "degraded"
        
        response_data = {
            "status": overall_status,
            "timestamp": timestamp,
            "environment": ENVIRONMENT,
            "version": VERSION,
            "region": AWS_REGION,
            "services": services_health,
            "lambda": {
                "function_name": context.function_name if context else "unknown",
                "memory_limit": context.memory_limit_in_mb if context else "unknown",
                "request_id": context.aws_request_id if context else "unknown"
            }
        }
        
        logger.info(f"Health check: {overall_status}")
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return error_response(500, "Health check failed", {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "error": str(e)
        })


def check_services_health() -> Dict[str, str]:
    """
    Check health of dependent services.
    
    Returns:
        Dictionary with service names and their health status
    """
    services = {}
    
    # Check DynamoDB
    try:
        dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
        # Simple operation to check connectivity
        dynamodb.list_tables(Limit=1)
        services['dynamodb'] = 'healthy'
    except ClientError as e:
        logger.error(f"DynamoDB health check failed: {str(e)}")
        services['dynamodb'] = 'unhealthy'
    except Exception as e:
        logger.error(f"DynamoDB health check error: {str(e)}")
        services['dynamodb'] = 'unknown'
    
    return services


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create an error API response."""
    response_data = data or {'error': message}
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        },
        'body': json.dumps(response_data)
    }
