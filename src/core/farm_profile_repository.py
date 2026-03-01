"""Farm profile repository for DynamoDB operations.

This repository provides operations for farm profile management,
including CRUD operations for farmer agricultural data.
"""

from typing import Optional
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import logging

from src.models.farm import FarmProfile
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class FarmProfileRepository(BaseRepository):
    """Repository for farm profile CRUD operations."""
    
    def __init__(self, table_name: str = "FarmProfiles", region_name: str = "us-east-1"):
        """
        Initialize FarmProfileRepository.
        
        Args:
            table_name: Name of the FarmProfiles DynamoDB table (default: FarmProfiles)
            region_name: AWS region name (default: us-east-1)
        """
        super().__init__(table_name, region_name)
    
    def get_farm_profile(self, user_id: str) -> FarmProfile:
        """
        Retrieve a farm profile by user_id.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            FarmProfile object
            
        Raises:
            ItemNotFoundError: If farm profile not found
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Farm profile for user {user_id} not found")
            
            # Deserialize and convert to FarmProfile
            item = self._deserialize_item(response['Item'])
            return FarmProfile(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get farm profile {user_id}")
    
    def create_farm_profile(self, farm_profile: FarmProfile) -> FarmProfile:
        """
        Create a new farm profile.
        
        Args:
            farm_profile: FarmProfile object to create
            
        Returns:
            Created FarmProfile object
            
        Raises:
            DynamoDBRepositoryError: If creation fails or profile already exists
        """
        try:
            # Serialize the profile
            item = self._serialize_item(farm_profile.model_dump())
            
            # Add timestamps
            now = datetime.now(timezone.utc).isoformat()
            item['created_at'] = now
            item['updated_at'] = now
            
            # Put item with condition that user_id doesn't exist
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            logger.info(f"Created farm profile for user: {farm_profile.user_id}")
            return farm_profile
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(
                    f"Farm profile for user {farm_profile.user_id} already exists"
                )
            self._handle_client_error(e, "create farm profile")
    
    def update_farm_profile(self, farm_profile: FarmProfile) -> FarmProfile:
        """
        Update an existing farm profile.
        
        Args:
            farm_profile: FarmProfile object with updated data
            
        Returns:
            Updated FarmProfile object
            
        Raises:
            ItemNotFoundError: If farm profile not found
            DynamoDBRepositoryError: If update fails
        """
        try:
            # Serialize the profile
            item = self._serialize_item(farm_profile.model_dump())
            
            # Update timestamp
            item['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Put item with condition that user_id exists
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(user_id)'
            )
            
            logger.info(f"Updated farm profile for user: {farm_profile.user_id}")
            return farm_profile
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Farm profile for user {farm_profile.user_id} not found")
            self._handle_client_error(e, f"update farm profile {farm_profile.user_id}")
    
    def delete_farm_profile(self, user_id: str) -> None:
        """
        Delete a farm profile.
        
        Args:
            user_id: Unique user identifier
            
        Raises:
            ItemNotFoundError: If farm profile not found
            DynamoDBRepositoryError: If deletion fails
        """
        try:
            self.table.delete_item(
                Key={'user_id': user_id},
                ConditionExpression='attribute_exists(user_id)'
            )
            
            logger.info(f"Deleted farm profile for user: {user_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Farm profile for user {user_id} not found")
            self._handle_client_error(e, f"delete farm profile {user_id}")
    
    def farm_profile_exists(self, user_id: str) -> bool:
        """
        Check if a farm profile exists for the given user_id.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if farm profile exists, False otherwise
        """
        try:
            response = self.table.get_item(
                Key={'user_id': user_id},
                ProjectionExpression='user_id'
            )
            return 'Item' in response
        except ClientError as e:
            logger.error(f"Error checking farm profile existence: {e}")
            return False
