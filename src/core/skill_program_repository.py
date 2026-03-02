"""Skill program repository for DynamoDB operations."""

from typing import List, Optional
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging

from src.models.skill import SkillProgram
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class SkillProgramFilters:
    """Filters for skill program search operations."""
    
    def __init__(
        self,
        category: Optional[str] = None,
        state: Optional[str] = None,
        mode: Optional[str] = None,
        max_cost: Optional[float] = None,
        certification: Optional[bool] = None,
        placement_support: Optional[bool] = None
    ):
        """
        Initialize skill program filters.
        
        Args:
            category: Filter by program category (technical, vocational, digital, entrepreneurship)
            state: Filter by state
            mode: Filter by delivery mode (in-person, online, hybrid)
            max_cost: Maximum program cost
            certification: Filter by certification availability
            placement_support: Filter by placement support availability
        """
        self.category = category
        self.state = state
        self.mode = mode
        self.max_cost = max_cost
        self.certification = certification
        self.placement_support = placement_support


class SkillProgramRepository(BaseRepository):
    """Repository for skill program operations."""
    
    def __init__(self, table_name: str = "SkillPrograms", region_name: str = "us-east-1"):
        """
        Initialize SkillProgramRepository.
        
        Args:
            table_name: Name of the SkillPrograms DynamoDB table
            region_name: AWS region name
        """
        super().__init__(table_name, region_name)
    
    def create(self, program: SkillProgram) -> SkillProgram:
        """
        Create a new skill program in DynamoDB.
        
        Args:
            program: SkillProgram object to create
            
        Returns:
            Created SkillProgram object
            
        Raises:
            DynamoDBRepositoryError: If creation fails
        """
        try:
            item = self._serialize_item(program.model_dump())
            
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(program_id)'
            )
            
            logger.info(f"Created skill program: {program.program_id}")
            return program
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(f"Program with ID {program.program_id} already exists")
            self._handle_client_error(e, "create skill program")
    
    def get(self, program_id: str) -> SkillProgram:
        """
        Retrieve a skill program by program_id.
        
        Args:
            program_id: Unique program identifier
            
        Returns:
            SkillProgram object
            
        Raises:
            ItemNotFoundError: If program not found
        """
        try:
            response = self.table.get_item(Key={'program_id': program_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Program with ID {program_id} not found")
            
            item = self._deserialize_item(response['Item'])
            return SkillProgram(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get skill program {program_id}")
    
    def search_programs(
        self,
        query: Optional[str] = None,
        filters: Optional[SkillProgramFilters] = None,
        limit: int = 50
    ) -> List[SkillProgram]:
        """
        Search skill programs by keywords and filters.
        
        Args:
            query: Search query string
            filters: SkillProgramFilters object
            limit: Maximum number of results
            
        Returns:
            List of matching SkillProgram objects
        """
        filters = filters or SkillProgramFilters()
        
        try:
            if filters.category:
                return self._query_by_category(filters.category, query, filters, limit)
            else:
                return self._scan_with_filters(query, filters, limit)
                
        except ClientError as e:
            self._handle_client_error(e, "search skill programs")
    
    def _query_by_category(
        self,
        category: str,
        query: Optional[str],
        filters: SkillProgramFilters,
        limit: int
    ) -> List[SkillProgram]:
        """Query programs by category using GSI."""
        try:
            filter_expr = None
            
            if filters.state:
                filter_expr = Attr('location').exists() & Attr('location.state').eq(filters.state)
            
            if filters.mode:
                mode_filter = Attr('mode').eq(filters.mode)
                filter_expr = mode_filter if filter_expr is None else filter_expr & mode_filter
            
            if filters.max_cost is not None:
                cost_filter = Attr('cost').lte(filters.max_cost)
                filter_expr = cost_filter if filter_expr is None else filter_expr & cost_filter
            
            if filters.certification is not None:
                cert_filter = Attr('certification').eq(filters.certification)
                filter_expr = cert_filter if filter_expr is None else filter_expr & cert_filter
            
            if filters.placement_support is not None:
                placement_filter = Attr('placement_support').eq(filters.placement_support)
                filter_expr = placement_filter if filter_expr is None else filter_expr & placement_filter
            
            if query:
                keyword_filter = self._build_keyword_filter(query)
                filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
            
            query_params = {
                'IndexName': 'category-index',
                'KeyConditionExpression': Key('category').eq(category),
                'Limit': limit
            }
            
            if filter_expr is not None:
                query_params['FilterExpression'] = filter_expr
            
            response = self.table.query(**query_params)
            
            programs = []
            for item in response.get('Items', []):
                deserialized = self._deserialize_item(item)
                programs.append(SkillProgram(**deserialized))
            
            return programs
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                logger.warning("category-index GSI not found, falling back to scan")
                return self._scan_with_filters(query, filters, limit)
            raise
    
    def _scan_with_filters(
        self,
        query: Optional[str],
        filters: SkillProgramFilters,
        limit: int
    ) -> List[SkillProgram]:
        """Scan table with filters."""
        filter_expr = None
        
        if filters.category:
            filter_expr = Attr('category').eq(filters.category)
        
        if filters.state:
            state_filter = Attr('location').exists() & Attr('location.state').eq(filters.state)
            filter_expr = state_filter if filter_expr is None else filter_expr & state_filter
        
        if filters.mode:
            mode_filter = Attr('mode').eq(filters.mode)
            filter_expr = mode_filter if filter_expr is None else filter_expr & mode_filter
        
        if filters.max_cost is not None:
            cost_filter = Attr('cost').lte(filters.max_cost)
            filter_expr = cost_filter if filter_expr is None else filter_expr & cost_filter
        
        if filters.certification is not None:
            cert_filter = Attr('certification').eq(filters.certification)
            filter_expr = cert_filter if filter_expr is None else filter_expr & cert_filter
        
        if filters.placement_support is not None:
            placement_filter = Attr('placement_support').eq(filters.placement_support)
            filter_expr = placement_filter if filter_expr is None else filter_expr & placement_filter
        
        if query:
            keyword_filter = self._build_keyword_filter(query)
            filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
        
        scan_params = {'Limit': limit}
        if filter_expr is not None:
            scan_params['FilterExpression'] = filter_expr
        
        response = self.table.scan(**scan_params)
        
        programs = []
        for item in response.get('Items', []):
            deserialized = self._deserialize_item(item)
            programs.append(SkillProgram(**deserialized))
        
        return programs
    
    def _build_keyword_filter(self, query: str):
        """Build filter expression for keyword search."""
        query_lower = query.lower()
        return (
            Attr('name').contains(query) |
            Attr('description').contains(query) |
            Attr('name').contains(query_lower) |
            Attr('description').contains(query_lower)
        )
