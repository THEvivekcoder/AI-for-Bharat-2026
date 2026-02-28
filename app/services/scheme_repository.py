"""Scheme repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.scheme import Scheme, SchemeTranslation
from app.schemas.scheme import SchemeCreate, SchemeUpdate, SchemeFilters
from app.exceptions import DatabaseException, DataNotFoundException
from app.logging_config import logger
from datetime import datetime
import uuid


class SchemeRepository:
    """Repository for scheme database operations"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
    
    def search_schemes(
        self, 
        filters: SchemeFilters,
        limit: int = 100,
        offset: int = 0
    ) -> List[Scheme]:
        """
        Search schemes by keywords and filters
        
        Args:
            filters: SchemeFilters with optional category, state, department, query
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching schemes
            
        Raises:
            DatabaseException: If database query fails
        """
        try:
            query = self.db.query(Scheme).options(joinedload(Scheme.translations))
            
            # Apply filters
            if filters.category:
                query = query.filter(Scheme.category == filters.category)
            
            if filters.state:
                query = query.filter(
                    or_(
                        Scheme.state == filters.state,
                        Scheme.state.is_(None)  # Include central schemes
                    )
                )
            
            if filters.department:
                query = query.filter(Scheme.department == filters.department)
            
            if filters.query:
                # Text search in name and description
                search_term = f"%{filters.query}%"
                query = query.filter(
                    or_(
                        Scheme.name.ilike(search_term),
                        Scheme.description.ilike(search_term)
                    )
                )
            
            # Order by created_at descending (newest first)
            query = query.order_by(Scheme.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            results = query.all()
            
            if not results:
                logger.info(f"No schemes found matching filters: {filters}")
            
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in search_schemes: {str(e)}")
            raise DatabaseException(
                message="Failed to search schemes",
                operation="read"
            )
    
    def get_scheme_by_id(self, scheme_id: str) -> Optional[Scheme]:
        """
        Retrieve scheme details by ID
        
        Args:
            scheme_id: UUID of the scheme
            
        Returns:
            Scheme object or None if not found
            
        Raises:
            DatabaseException: If database query fails
            DataNotFoundException: If scheme not found
        """
        try:
            try:
                scheme_uuid = uuid.UUID(scheme_id)
            except ValueError:
                raise DataNotFoundException(
                    message=f"Invalid scheme ID format: {scheme_id}",
                    suggestions=["Check the scheme ID and try again"]
                )
            
            scheme = self.db.query(Scheme).options(
                joinedload(Scheme.translations)
            ).filter(
                Scheme.scheme_id == scheme_uuid
            ).first()
            
            if not scheme:
                raise DataNotFoundException(
                    message=f"Scheme not found: {scheme_id}",
                    suggestions=["Search for schemes by category or keywords"]
                )
            
            return scheme
            
        except DataNotFoundException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_scheme_by_id: {str(e)}")
            raise DatabaseException(
                message="Failed to retrieve scheme",
                operation="read"
            )
    
    def get_all_schemes(
        self, 
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Scheme]:
        """
        Get all schemes, optionally filtered by category
        
        Args:
            category: Optional category filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of schemes
        """
        query = self.db.query(Scheme).options(joinedload(Scheme.translations))
        
        if category:
            query = query.filter(Scheme.category == category)
        
        query = query.order_by(Scheme.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def create_scheme(self, scheme_data: SchemeCreate) -> Scheme:
        """
        Create a new scheme
        
        Args:
            scheme_data: SchemeCreate schema with scheme information
            
        Returns:
            Created Scheme object
            
        Raises:
            DatabaseException: If database operation fails
        """
        try:
            # Convert eligibility criteria to dict
            eligibility_dict = scheme_data.eligibility_criteria.model_dump(exclude_none=True)
            
            # Create scheme
            scheme = Scheme(
                scheme_id=uuid.uuid4(),
                name=scheme_data.name,
                category=scheme_data.category,
                description=scheme_data.description,
                benefits=scheme_data.benefits,
                eligibility_criteria=eligibility_dict,
                required_documents=scheme_data.required_documents,
                application_process=scheme_data.application_process,
                application_url=scheme_data.application_url,
                department=scheme_data.department,
                state=scheme_data.state,
                source_url=scheme_data.source_url,
                last_updated=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            self.db.add(scheme)
            
            # Add translations if provided
            if scheme_data.translations:
                for trans_data in scheme_data.translations:
                    translation = SchemeTranslation(
                        translation_id=uuid.uuid4(),
                        scheme_id=scheme.scheme_id,
                        language=trans_data.language,
                        name=trans_data.name,
                        description=trans_data.description,
                        benefits=trans_data.benefits
                    )
                    self.db.add(translation)
            
            self.db.commit()
            self.db.refresh(scheme)
            
            logger.info(f"Created scheme: {scheme.scheme_id}")
            return scheme
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating scheme: {str(e)}")
            raise DatabaseException(
                message="Failed to create scheme (duplicate or constraint violation)",
                operation="create"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating scheme: {str(e)}")
            raise DatabaseException(
                message="Failed to create scheme",
                operation="create"
            )
    
    def update_scheme(self, scheme_id: str, scheme_data: SchemeUpdate) -> Optional[Scheme]:
        """
        Update scheme information
        
        Args:
            scheme_id: UUID of the scheme
            scheme_data: SchemeUpdate schema with updated fields
            
        Returns:
            Updated Scheme object or None if not found
        """
        scheme = self.get_scheme_by_id(scheme_id)
        
        if not scheme:
            return None
        
        # Update fields if provided
        update_data = scheme_data.model_dump(exclude_unset=True, exclude_none=False)
        
        for field, value in update_data.items():
            if field == 'eligibility_criteria' and value is not None:
                # Convert Pydantic model to dict
                value = value.model_dump(exclude_none=True)
            setattr(scheme, field, value)
        
        # Update last_updated timestamp
        scheme.last_updated = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def delete_scheme(self, scheme_id: str) -> bool:
        """
        Delete a scheme
        
        Args:
            scheme_id: UUID of the scheme
            
        Returns:
            True if deleted, False if not found
        """
        scheme = self.get_scheme_by_id(scheme_id)
        
        if not scheme:
            return False
        
        self.db.delete(scheme)
        self.db.commit()
        
        return True

    def mark_scheme_as_verified(
        self, 
        scheme_id: str, 
        verification_source: str
    ) -> Optional[Scheme]:
        """
        Mark a scheme as verified
        
        Args:
            scheme_id: UUID of the scheme
            verification_source: Source used for verification
            
        Returns:
            Updated Scheme object or None if not found
        """
        from app.services.verification_tracker import VerificationTracker
        
        scheme = self.get_scheme_by_id(scheme_id)
        
        if not scheme:
            return None
        
        # Update verification fields
        verification_data = VerificationTracker.mark_as_verified(verification_source)
        for field, value in verification_data.items():
            setattr(scheme, field, value)
        
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def mark_scheme_as_unverified(
        self, 
        scheme_id: str, 
        source: Optional[str] = None
    ) -> Optional[Scheme]:
        """
        Mark a scheme as unverified with source attribution
        
        Args:
            scheme_id: UUID of the scheme
            source: Source attribution for unverified data
            
        Returns:
            Updated Scheme object or None if not found
        """
        from app.services.verification_tracker import VerificationTracker
        
        scheme = self.get_scheme_by_id(scheme_id)
        
        if not scheme:
            return None
        
        # Update verification fields
        verification_data = VerificationTracker.mark_as_unverified(source)
        for field, value in verification_data.items():
            setattr(scheme, field, value)
        
        self.db.commit()
        self.db.refresh(scheme)
        
        return scheme
    
    def get_schemes_needing_verification(
        self, 
        reverification_days: int = 30,
        limit: int = 100
    ) -> List[Scheme]:
        """
        Get schemes that need verification or reverification
        
        Args:
            reverification_days: Number of days before reverification needed
            limit: Maximum number of results
            
        Returns:
            List of schemes needing verification
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=reverification_days)
        
        query = self.db.query(Scheme).filter(
            or_(
                Scheme.verified_at.is_(None),
                Scheme.verified_at < cutoff_date,
                Scheme.verification_status != 'verified'
            )
        ).order_by(Scheme.last_updated.asc()).limit(limit)
        
        return query.all()
