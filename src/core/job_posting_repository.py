"""Job posting repository for DynamoDB operations."""

from typing import List, Optional
from datetime import date
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging

from src.models.skill import JobPosting
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class JobPostingFilters:
    """Filters for job posting search operations."""
    
    def __init__(
        self,
        department: Optional[str] = None,
        state: Optional[str] = None,
        education: Optional[List[str]] = None,
        deadline_after: Optional[date] = None
    ):
        """
        Initialize job posting filters.
        
        Args:
            department: Filter by government department
            state: Filter by state
            education: Filter by required education qualifications
            deadline_after: Filter jobs with deadline after this date
        """
        self.department = department
        self.state = state
        self.education = education or []
        self.deadline_after = deadline_after


class JobPostingRepository(BaseRepository):
    """Repository for job posting operations."""
    
    def __init__(self, table_name: str = "JobPostings", region_name: str = "us-east-1"):
        """
        Initialize JobPostingRepository.
        
        Args:
            table_name: Name of the JobPostings DynamoDB table
            region_name: AWS region name
        """
        super().__init__(table_name, region_name)
    
    def create(self, job: JobPosting) -> JobPosting:
        """
        Create a new job posting in DynamoDB.
        
        Args:
            job: JobPosting object to create
            
        Returns:
            Created JobPosting object
            
        Raises:
            DynamoDBRepositoryError: If creation fails
        """
        try:
            item = self._serialize_item(job.model_dump())
            
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(job_id)'
            )
            
            logger.info(f"Created job posting: {job.job_id}")
            return job
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(f"Job with ID {job.job_id} already exists")
            self._handle_client_error(e, "create job posting")
    
    def get(self, job_id: str) -> JobPosting:
        """
        Retrieve a job posting by job_id.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            JobPosting object
            
        Raises:
            ItemNotFoundError: If job not found
        """
        try:
            response = self.table.get_item(Key={'job_id': job_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Job with ID {job_id} not found")
            
            item = self._deserialize_item(response['Item'])
            return JobPosting(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get job posting {job_id}")
    
    def search_jobs(
        self,
        query: Optional[str] = None,
        filters: Optional[JobPostingFilters] = None,
        limit: int = 50
    ) -> List[JobPosting]:
        """
        Search job postings by keywords and filters.
        
        Args:
            query: Search query string
            filters: JobPostingFilters object
            limit: Maximum number of results
            
        Returns:
            List of matching JobPosting objects
        """
        filters = filters or JobPostingFilters()
        
        try:
            if filters.department:
                return self._query_by_department(filters.department, query, filters, limit)
            else:
                return self._scan_with_filters(query, filters, limit)
                
        except ClientError as e:
            self._handle_client_error(e, "search job postings")
    
    def _query_by_department(
        self,
        department: str,
        query: Optional[str],
        filters: JobPostingFilters,
        limit: int
    ) -> List[JobPosting]:
        """Query jobs by department using GSI."""
        try:
            filter_expr = None
            
            if filters.state:
                filter_expr = Attr('location').exists() & Attr('location.state').eq(filters.state)
            
            if filters.deadline_after:
                deadline_str = filters.deadline_after.isoformat()
                deadline_filter = Attr('application_deadline').gte(deadline_str)
                filter_expr = deadline_filter if filter_expr is None else filter_expr & deadline_filter
            
            if filters.education:
                # Check if any of the user's education qualifications match job requirements
                education_filter = None
                for edu in filters.education:
                    edu_check = Attr('qualifications.education').contains(edu)
                    education_filter = edu_check if education_filter is None else education_filter | edu_check
                
                if education_filter:
                    filter_expr = education_filter if filter_expr is None else filter_expr & education_filter
            
            if query:
                keyword_filter = self._build_keyword_filter(query)
                filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
            
            query_params = {
                'IndexName': 'department-index',
                'KeyConditionExpression': Key('department').eq(department),
                'Limit': limit
            }
            
            if filter_expr is not None:
                query_params['FilterExpression'] = filter_expr
            
            response = self.table.query(**query_params)
            
            jobs = []
            for item in response.get('Items', []):
                deserialized = self._deserialize_item(item)
                jobs.append(JobPosting(**deserialized))
            
            return jobs
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                logger.warning("department-index GSI not found, falling back to scan")
                return self._scan_with_filters(query, filters, limit)
            raise
    
    def _scan_with_filters(
        self,
        query: Optional[str],
        filters: JobPostingFilters,
        limit: int
    ) -> List[JobPosting]:
        """Scan table with filters."""
        filter_expr = None
        
        if filters.department:
            filter_expr = Attr('department').eq(filters.department)
        
        if filters.state:
            state_filter = Attr('location').exists() & Attr('location.state').eq(filters.state)
            filter_expr = state_filter if filter_expr is None else filter_expr & state_filter
        
        if filters.deadline_after:
            deadline_str = filters.deadline_after.isoformat()
            deadline_filter = Attr('application_deadline').gte(deadline_str)
            filter_expr = deadline_filter if filter_expr is None else filter_expr & deadline_filter
        
        if filters.education:
            education_filter = None
            for edu in filters.education:
                edu_check = Attr('qualifications.education').contains(edu)
                education_filter = edu_check if education_filter is None else education_filter | edu_check
            
            if education_filter:
                filter_expr = education_filter if filter_expr is None else filter_expr & education_filter
        
        if query:
            keyword_filter = self._build_keyword_filter(query)
            filter_expr = keyword_filter if filter_expr is None else filter_expr & keyword_filter
        
        scan_params = {'Limit': limit}
        if filter_expr is not None:
            scan_params['FilterExpression'] = filter_expr
        
        response = self.table.scan(**scan_params)
        
        jobs = []
        for item in response.get('Items', []):
            deserialized = self._deserialize_item(item)
            jobs.append(JobPosting(**deserialized))
        
        return jobs
    
    def _build_keyword_filter(self, query: str):
        """Build filter expression for keyword search."""
        query_lower = query.lower()
        return (
            Attr('title').contains(query) |
            Attr('description').contains(query) |
            Attr('title').contains(query_lower) |
            Attr('description').contains(query_lower)
        )
    
    def get_active_jobs(self, limit: int = 50) -> List[JobPosting]:
        """
        Get all active job postings (deadline not passed).
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of active JobPosting objects
        """
        today = date.today()
        filters = JobPostingFilters(deadline_after=today)
        return self.search_jobs(query=None, filters=filters, limit=limit)
