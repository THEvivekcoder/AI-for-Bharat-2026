"""Base repository class for DynamoDB operations."""

from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class DynamoDBRepositoryError(Exception):
    """Base exception for DynamoDB repository errors."""
    pass


class ItemNotFoundError(DynamoDBRepositoryError):
    """Exception raised when an item is not found in DynamoDB."""
    pass


class BaseRepository:
    """Base repository class with common DynamoDB operations."""
    
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """
        Initialize repository with DynamoDB table.
        
        Args:
            table_name: Name of the DynamoDB table
            region_name: AWS region name (default: us-east-1)
        """
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        self.client = boto3.client('dynamodb', region_name=region_name)
    
    def _handle_client_error(self, error: ClientError, operation: str) -> None:
        """
        Handle DynamoDB client errors with appropriate logging and exceptions.
        
        Args:
            error: The ClientError exception
            operation: Description of the operation that failed
            
        Raises:
            ItemNotFoundError: If the item was not found
            DynamoDBRepositoryError: For other DynamoDB errors
        """
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']
        
        logger.error(f"DynamoDB error during {operation}: {error_code} - {error_message}")
        
        if error_code == 'ResourceNotFoundException':
            raise ItemNotFoundError(f"Table {self.table_name} not found")
        elif error_code == 'ConditionalCheckFailedException':
            raise ItemNotFoundError(f"Item not found or condition failed during {operation}")
        else:
            raise DynamoDBRepositoryError(f"DynamoDB error during {operation}: {error_message}")
    
    def _serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize item for DynamoDB storage.
        Converts datetime and date objects to ISO format strings.
        
        Args:
            item: Dictionary to serialize
            
        Returns:
            Serialized dictionary
        """
        from datetime import datetime, date
        
        serialized = {}
        for key, value in item.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, date):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_item(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_item(v) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                serialized[key] = value
        return serialized
    
    def _deserialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize item from DynamoDB storage.
        Converts ISO format strings back to datetime or date objects where appropriate.
        
        Args:
            item: Dictionary to deserialize
            
        Returns:
            Deserialized dictionary
        """
        from datetime import datetime, date
        
        deserialized = {}
        for key, value in item.items():
            # Try to parse datetime fields
            if isinstance(value, str) and key in ['created_at', 'updated_at', 'last_updated']:
                try:
                    deserialized[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    deserialized[key] = value
            # Try to parse date fields
            elif isinstance(value, str) and key in ['application_deadline', 'posted_date', 'date']:
                try:
                    deserialized[key] = date.fromisoformat(value)
                except (ValueError, AttributeError):
                    deserialized[key] = value
            elif isinstance(value, dict):
                deserialized[key] = self._deserialize_item(value)
            elif isinstance(value, list):
                deserialized[key] = [
                    self._deserialize_item(v) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                deserialized[key] = value
        return deserialized
