"""Profile repository for DynamoDB operations.

This repository provides specialized operations for user profile management,
including get and update operations with additional business logic.
"""

from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from datetime import datetime
import logging

from src.models.user import UserProfile
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class ProfileRepository(BaseRepository):
    """Repository for user profile get/update operations with business logic."""
    
    def __init__(self, table_name: str = "UserProfiles", region_name: str = "us-east-1"):
        """
        Initialize ProfileRepository.
        
        Args:
            table_name: Name of the UserProfiles DynamoDB table (default: UserProfiles)
            region_name: AWS region name (default: us-east-1)
        """
        super().__init__(table_name, region_name)
    
    def get_profile(self, user_id: str) -> UserProfile:
        """
        Retrieve a user profile by user_id.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile object
            
        Raises:
            ItemNotFoundError: If profile not found
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Profile for user {user_id} not found")
            
            # Deserialize and convert to UserProfile
            item = self._deserialize_item(response['Item'])
            return UserProfile(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get profile {user_id}")
    
    def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
        create_if_not_exists: bool = False
    ) -> UserProfile:
        """
        Update specific fields in a user profile.
        
        Args:
            user_id: Unique user identifier
            updates: Dictionary of fields to update
            create_if_not_exists: If True, create profile if it doesn't exist
            
        Returns:
            Updated UserProfile object
            
        Raises:
            ItemNotFoundError: If profile not found and create_if_not_exists is False
            DynamoDBRepositoryError: If update fails
        """
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Build update expression
            update_expr_parts = []
            expr_attr_names = {}
            expr_attr_values = {}
            
            for i, (key, value) in enumerate(updates.items()):
                attr_name = f"#attr{i}"
                attr_value = f":val{i}"
                update_expr_parts.append(f"{attr_name} = {attr_value}")
                expr_attr_names[attr_name] = key
                
                # Serialize value if it's a complex type
                if isinstance(value, (dict, list)):
                    expr_attr_values[attr_value] = self._serialize_item({key: value})[key]
                else:
                    expr_attr_values[attr_value] = value
            
            update_expr = "SET " + ", ".join(update_expr_parts)
            
            # Prepare update parameters
            update_params = {
                'Key': {'user_id': user_id},
                'UpdateExpression': update_expr,
                'ExpressionAttributeNames': expr_attr_names,
                'ExpressionAttributeValues': expr_attr_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            # Add condition expression if not creating
            if not create_if_not_exists:
                update_params['ConditionExpression'] = 'attribute_exists(user_id)'
            
            response = self.table.update_item(**update_params)
            
            # Convert response to UserProfile
            item = self._deserialize_item(response['Attributes'])
            logger.info(f"Updated profile for user: {user_id}")
            return UserProfile(**item)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Profile for user {user_id} not found")
            self._handle_client_error(e, f"update profile {user_id}")
    
    def create_profile(self, user_profile: UserProfile) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            user_profile: UserProfile object to create
            
        Returns:
            Created UserProfile object
            
        Raises:
            DynamoDBRepositoryError: If creation fails or profile already exists
        """
        try:
            # Serialize the profile
            item = self._serialize_item(user_profile.model_dump())
            
            # Put item with condition that user_id doesn't exist
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            logger.info(f"Created profile for user: {user_profile.user_id}")
            return user_profile
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(f"Profile for user {user_profile.user_id} already exists")
            self._handle_client_error(e, "create profile")
    
    def delete_profile(self, user_id: str) -> None:
        """
        Delete a user profile.
        
        Args:
            user_id: Unique user identifier
            
        Raises:
            ItemNotFoundError: If profile not found
            DynamoDBRepositoryError: If deletion fails
        """
        try:
            self.table.delete_item(
                Key={'user_id': user_id},
                ConditionExpression='attribute_exists(user_id)'
            )
            
            logger.info(f"Deleted profile for user: {user_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Profile for user {user_id} not found")
            self._handle_client_error(e, f"delete profile {user_id}")
    
    def update_location(self, user_id: str, location: Dict[str, Any]) -> UserProfile:
        """
        Update user location information.
        
        Args:
            user_id: Unique user identifier
            location: Location dictionary with state, district, pincode, etc.
            
        Returns:
            Updated UserProfile object
            
        Raises:
            ItemNotFoundError: If profile not found
            DynamoDBRepositoryError: If update fails
        """
        return self.update_profile(user_id, {'location': location})
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> UserProfile:
        """
        Update user preferences.
        
        Args:
            user_id: Unique user identifier
            preferences: Preferences dictionary
            
        Returns:
            Updated UserProfile object
            
        Raises:
            ItemNotFoundError: If profile not found
            DynamoDBRepositoryError: If update fails
        """
        return self.update_profile(user_id, {'preferences': preferences})
    
    def profile_exists(self, user_id: str) -> bool:
        """
        Check if a profile exists for the given user_id.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if profile exists, False otherwise
        """
        try:
            response = self.table.get_item(
                Key={'user_id': user_id},
                ProjectionExpression='user_id'
            )
            return 'Item' in response
        except ClientError as e:
            logger.error(f"Error checking profile existence: {e}")
            return False
