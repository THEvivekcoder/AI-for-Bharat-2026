"""User repository for DynamoDB operations."""

from typing import Optional
from botocore.exceptions import ClientError
import logging

from src.models.user import UserProfile
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user profile CRUD operations."""
    
    def __init__(self, table_name: str = "Users", region_name: str = "us-east-1"):
        """
        Initialize UserRepository.
        
        Args:
            table_name: Name of the Users DynamoDB table (default: Users)
            region_name: AWS region name (default: us-east-1)
        """
        super().__init__(table_name, region_name)
    
    def create(self, user_profile: UserProfile) -> UserProfile:
        """
        Create a new user profile in DynamoDB.
        
        Args:
            user_profile: UserProfile object to create
            
        Returns:
            Created UserProfile object
            
        Raises:
            DynamoDBRepositoryError: If creation fails
        """
        try:
            # Serialize the user profile
            item = self._serialize_item(user_profile.model_dump())
            
            # Put item in DynamoDB with condition that user_id doesn't exist
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            logger.info(f"Created user profile: {user_profile.user_id}")
            return user_profile
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(f"User with ID {user_profile.user_id} already exists")
            self._handle_client_error(e, "create user")
    
    def get(self, user_id: str) -> UserProfile:
        """
        Retrieve a user profile by user_id.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile object
            
        Raises:
            ItemNotFoundError: If user not found
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"User with ID {user_id} not found")
            
            # Deserialize and convert to UserProfile
            item = self._deserialize_item(response['Item'])
            return UserProfile(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get user {user_id}")
    
    def update(self, user_profile: UserProfile) -> UserProfile:
        """
        Update an existing user profile.
        
        Args:
            user_profile: UserProfile object with updated data
            
        Returns:
            Updated UserProfile object
            
        Raises:
            ItemNotFoundError: If user not found
            DynamoDBRepositoryError: If update fails
        """
        try:
            # Update the updated_at timestamp
            from datetime import datetime
            user_profile.updated_at = datetime.utcnow()
            
            # Serialize the user profile
            item = self._serialize_item(user_profile.model_dump())
            
            # Put item with condition that user_id exists
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(user_id)'
            )
            
            logger.info(f"Updated user profile: {user_profile.user_id}")
            return user_profile
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"User with ID {user_profile.user_id} not found")
            self._handle_client_error(e, f"update user {user_profile.user_id}")
    
    def delete(self, user_id: str) -> None:
        """
        Delete a user profile by user_id.
        
        Args:
            user_id: Unique user identifier
            
        Raises:
            ItemNotFoundError: If user not found
            DynamoDBRepositoryError: If deletion fails
        """
        try:
            self.table.delete_item(
                Key={'user_id': user_id},
                ConditionExpression='attribute_exists(user_id)'
            )
            
            logger.info(f"Deleted user profile: {user_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"User with ID {user_id} not found")
            self._handle_client_error(e, f"delete user {user_id}")
    
    def get_by_phone_number(self, phone_number: str) -> Optional[UserProfile]:
        """
        Retrieve a user profile by phone number.
        Note: This requires a GSI on phone_number in the DynamoDB table.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            UserProfile object if found, None otherwise
            
        Raises:
            DynamoDBRepositoryError: If query fails
        """
        try:
            response = self.table.query(
                IndexName='phone_number-index',
                KeyConditionExpression='phone_number = :phone',
                ExpressionAttributeValues={':phone': phone_number}
            )
            
            if not response.get('Items'):
                return None
            
            # Return the first matching user
            item = self._deserialize_item(response['Items'][0])
            return UserProfile(**item)
            
        except ClientError as e:
            # If GSI doesn't exist, fall back to scan (not recommended for production)
            if e.response['Error']['Code'] == 'ValidationException':
                logger.warning("phone_number-index GSI not found, falling back to scan")
                return self._scan_by_phone_number(phone_number)
            self._handle_client_error(e, f"query user by phone {phone_number}")
    
    def _scan_by_phone_number(self, phone_number: str) -> Optional[UserProfile]:
        """
        Fallback method to scan table for phone number.
        This is inefficient and should only be used if GSI is not available.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            UserProfile object if found, None otherwise
        """
        try:
            response = self.table.scan(
                FilterExpression='phone_number = :phone',
                ExpressionAttributeValues={':phone': phone_number}
            )
            
            if not response.get('Items'):
                return None
            
            item = self._deserialize_item(response['Items'][0])
            return UserProfile(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"scan user by phone {phone_number}")
