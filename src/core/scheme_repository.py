"""Scheme repository for DynamoDB operations."""

from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging

from src.models.scheme import Scheme
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class SchemeFilters:
    """Filters for scheme search operations."""
    
    def __init__(
        self,
        category: Optional[str] = None,
        state: Optional[str] = None,
        department: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ):
        """
        Initialize scheme filters.
        
        Args:
            category: Filter by scheme category
            state: Filter by state (None for central schemes)
            department: Filter by government department
            keywords: List of keywords to search in name/description
        """
        self.category = category
        self.state = state
        self.department = department
        self.keywords = keywords or []


class SchemeRepository(BaseRepository):
    """Repository for scheme search and filter operations."""
    
    def __init__(self, table_name: str = "Schemes", region_name: str = "us-east-1"):
        """
        Initialize SchemeRepository.
        
        Args:
            table_name: Name of the Schemes DynamoDB table (default: Schemes)
            region_name: AWS region name (default: us-east-1)
        """
        super().__init__(table_name, region_name)
    
    def create(self, scheme: Scheme) -> Scheme:
        """
        Create a new scheme in DynamoDB.
        
        Args:
            scheme: Scheme object to create
            
        Returns:
            Created Scheme object
            
        Raises:
            DynamoDBRepositoryError: If creation fails
        """
        try:
            # Serialize the scheme
            item = self._serialize_item(scheme.model_dump())
            
            # Put item in DynamoDB
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(scheme_id)'
            )
            
            logger.info(f"Created scheme: {scheme.scheme_id}")
            return scheme
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(f"Scheme with ID {scheme.scheme_id} already exists")
            self._handle_client_error(e, "create scheme")
    
    def get(self, scheme_id: str) -> Scheme:
        """
        Retrieve a scheme by scheme_id.
        
        Args:
            scheme_id: Unique scheme identifier
            
        Returns:
            Scheme object
            
        Raises:
            ItemNotFoundError: If scheme not found
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'scheme_id': scheme_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Scheme with ID {scheme_id} not found")
            
            # Deserialize and convert to Scheme
            item = self._deserialize_item(response['Item'])
            return Scheme(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get scheme {scheme_id}")
    
    def update(self, scheme: Scheme) -> Scheme:
        """
        Update an existing scheme.
        
        Args:
            scheme: Scheme object with updated data
            
        Returns:
            Updated Scheme object
            
        Raises:
            ItemNotFoundError: If scheme not found
            DynamoDBRepositoryError: If update fails
        """
        try:
            # Update the last_updated timestamp
            from datetime import datetime
            scheme.last_updated = datetime.utcnow()
            
            # Serialize the scheme
            item = self._serialize_item(scheme.model_dump())
            
            # Put item with condition that scheme_id exists
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(scheme_id)'
            )
            
            logger.info(f"Updated scheme: {scheme.scheme_id}")
            return scheme
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Scheme with ID {scheme.scheme_id} not found")
            self._handle_client_error(e, f"update scheme {scheme.scheme_id}")
    
    def delete(self, scheme_id: str) -> None:
        """
        Delete a scheme by scheme_id.
        
        Args:
            scheme_id: Unique scheme identifier
            
        Raises:
            ItemNotFoundError: If scheme not found
            DynamoDBRepositoryError: If deletion fails
        """
        try:
            self.table.delete_item(
                Key={'scheme_id': scheme_id},
                ConditionExpression='attribute_exists(scheme_id)'
            )
            
            logger.info(f"Deleted scheme: {scheme_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ItemNotFoundError(f"Scheme with ID {scheme_id} not found")
            self._handle_client_error(e, f"delete scheme {scheme_id}")
    
    def search_schemes(
        self,
        query: Optional[str] = None,
        filters: Optional[SchemeFilters] = None,
        limit: int = 50
    ) -> List[Scheme]:
        """
        Search schemes by keywords and filters.
        
        Args:
            query: Search query string (searches in name and description)
            filters: SchemeFilters object with filter criteria
            limit: Maximum number of results to return
            
        Returns:
            List of matching Scheme objects
            
        Raises:
            DynamoDBRepositoryError: If search fails
        """
        filters = filters or SchemeFilters()
        
        try:
            # If category filter is provided, use GSI for efficient query
            if filters.category:
                return self._query_by_category(filters.category, query, filters, limit)
            else:
                # Otherwise, scan the table with filters
                return self._scan_with_filters(query, filters, limit)
                
        except ClientError as e:
            self._handle_client_error(e, "search schemes")
    
    def _query_by_category(
        self,
        category: str,
        query: Optional[str],
        filters: SchemeFilters,
        limit: int
    ) -> List[Scheme]:
        """
        Query schemes by category using GSI.
        
        Args:
            category: Scheme category
            query: Search query string
            filters: Additional filters
            limit: Maximum results
            
        Returns:
            List of matching Scheme objects
        """
        try:
            # Build filter expression
            filter_expr = None
            expr_attr_values = {}
            
            # Add state filter
            if filters.state is not None:
                if filters.state == "":
                    # Empty string means central schemes (state is None)
                    filter_expr = Attr('state').not_exists() | Attr('state').eq(None)
                else:
                    filter_expr = Attr('state').eq(filters.state)
            
            # Add department filter
            if filters.department:
                dept_filter = Attr('department').eq(filters.department)
                filter_expr = dept_filter if filter_expr is None else filter_expr & dept_filter
            
            # Add keyword search filter
            if query:
                keyword_filter = self._build_keyword_filter(query)
                filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
            
            # Query using category GSI
            query_params = {
                'IndexName': 'category-index',
                'KeyConditionExpression': Key('category').eq(category),
                'Limit': limit
            }
            
            if filter_expr is not None:
                query_params['FilterExpression'] = filter_expr
            
            response = self.table.query(**query_params)
            
            # Convert items to Scheme objects
            schemes = []
            for item in response.get('Items', []):
                deserialized = self._deserialize_item(item)
                schemes.append(Scheme(**deserialized))
            
            return schemes
            
        except ClientError as e:
            # If GSI doesn't exist, fall back to scan
            if e.response['Error']['Code'] == 'ValidationException':
                logger.warning("category-index GSI not found, falling back to scan")
                return self._scan_with_filters(query, filters, limit)
            raise
    
    def _scan_with_filters(
        self,
        query: Optional[str],
        filters: SchemeFilters,
        limit: int
    ) -> List[Scheme]:
        """
        Scan table with filters (fallback when GSI not available).
        
        Args:
            query: Search query string
            filters: Filter criteria
            limit: Maximum results
            
        Returns:
            List of matching Scheme objects
        """
        # Build filter expression
        filter_expr = None
        
        # Add category filter
        if filters.category:
            filter_expr = Attr('category').eq(filters.category)
        
        # Add state filter
        if filters.state is not None:
            if filters.state == "":
                state_filter = Attr('state').not_exists() | Attr('state').eq(None)
            else:
                state_filter = Attr('state').eq(filters.state)
            filter_expr = state_filter if filter_expr is None else filter_expr & state_filter
        
        # Add department filter
        if filters.department:
            dept_filter = Attr('department').eq(filters.department)
            filter_expr = dept_filter if filter_expr is None else filter_expr & dept_filter
        
        # Add keyword search filter
        if query:
            keyword_filter = self._build_keyword_filter(query)
            filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
        
        # Scan table
        scan_params = {'Limit': limit}
        if filter_expr is not None:
            scan_params['FilterExpression'] = filter_expr
        
        response = self.table.scan(**scan_params)
        
        # Convert items to Scheme objects
        schemes = []
        for item in response.get('Items', []):
            deserialized = self._deserialize_item(item)
            schemes.append(Scheme(**deserialized))
        
        return schemes
    
    def _build_keyword_filter(self, query: str):
        """
        Build filter expression for keyword search.
        Searches in name and description fields.
        
        Args:
            query: Search query string
            
        Returns:
            Filter expression
        """
        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()
        
        # Search in name and description (case-insensitive using contains)
        return (
            Attr('name').contains(query) |
            Attr('description').contains(query) |
            Attr('name').contains(query_lower) |
            Attr('description').contains(query_lower)
        )
    
    def get_all_schemes(self, category: Optional[str] = None, limit: int = 100) -> List[Scheme]:
        """
        Get all schemes, optionally filtered by category.
        
        Args:
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of Scheme objects
            
        Raises:
            DynamoDBRepositoryError: If retrieval fails
        """
        filters = SchemeFilters(category=category) if category else None
        return self.search_schemes(query=None, filters=filters, limit=limit)
    
    def get_schemes_by_state(self, state: Optional[str], limit: int = 50) -> List[Scheme]:
        """
        Get schemes for a specific state or central schemes.
        
        Args:
            state: State name (None or empty string for central schemes)
            limit: Maximum number of results
            
        Returns:
            List of Scheme objects
            
        Raises:
            DynamoDBRepositoryError: If retrieval fails
        """
        filters = SchemeFilters(state=state if state else "")
        return self.search_schemes(query=None, filters=filters, limit=limit)
