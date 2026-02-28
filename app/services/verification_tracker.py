"""Verification tracking and uncertainty indicators for data freshness"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status values"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING = "pending"


class DataFreshnessLevel(str, Enum):
    """Data freshness levels"""
    FRESH = "fresh"  # Updated within last 7 days
    RECENT = "recent"  # Updated within last 30 days
    STALE = "stale"  # Updated more than 30 days ago
    UNKNOWN = "unknown"  # No update timestamp


class VerificationTracker:
    """Utility class for tracking data verification and freshness"""
    
    @staticmethod
    def calculate_data_age_days(last_updated: Optional[datetime]) -> Optional[int]:
        """
        Calculate the age of data in days since last update
        
        Args:
            last_updated: Timestamp of last update
            
        Returns:
            Number of days since last update, or None if no timestamp
        """
        if not last_updated:
            return None
        
        now = datetime.utcnow()
        delta = now - last_updated
        return delta.days
    
    @staticmethod
    def get_freshness_level(last_updated: Optional[datetime]) -> DataFreshnessLevel:
        """
        Determine the freshness level of data
        
        Args:
            last_updated: Timestamp of last update
            
        Returns:
            DataFreshnessLevel enum value
        """
        if not last_updated:
            return DataFreshnessLevel.UNKNOWN
        
        age_days = VerificationTracker.calculate_data_age_days(last_updated)
        
        if age_days is None:
            return DataFreshnessLevel.UNKNOWN
        elif age_days <= 7:
            return DataFreshnessLevel.FRESH
        elif age_days <= 30:
            return DataFreshnessLevel.RECENT
        else:
            return DataFreshnessLevel.STALE
    
    @staticmethod
    def is_verified(verification_status: Optional[str]) -> bool:
        """
        Check if data is verified
        
        Args:
            verification_status: Verification status string
            
        Returns:
            True if verified, False otherwise
        """
        return verification_status == VerificationStatus.VERIFIED
    
    @staticmethod
    def add_uncertainty_indicators(
        data: Dict[str, Any],
        last_updated: Optional[datetime] = None,
        verification_status: Optional[str] = None,
        verification_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add uncertainty indicators to response data
        
        Args:
            data: Response data dictionary
            last_updated: Timestamp of last update
            verification_status: Verification status
            verification_source: Source used for verification
            
        Returns:
            Data dictionary with added uncertainty indicators
        """
        # Calculate data age
        data_age_days = VerificationTracker.calculate_data_age_days(last_updated)
        freshness_level = VerificationTracker.get_freshness_level(last_updated)
        is_verified = VerificationTracker.is_verified(verification_status)
        
        # Add indicators
        data['is_verified'] = is_verified
        data['data_age_days'] = data_age_days
        data['freshness_level'] = freshness_level.value
        
        # Add verification source if unverified
        if not is_verified and verification_source:
            data['verification_source'] = verification_source
        
        # Add warning message for stale or unverified data
        warnings = []
        if freshness_level == DataFreshnessLevel.STALE:
            warnings.append(f"This information was last updated {data_age_days} days ago and may be outdated.")
        elif freshness_level == DataFreshnessLevel.UNKNOWN:
            warnings.append("The update date for this information is unknown. Please verify independently.")
        
        if not is_verified:
            warnings.append("This information has not been verified against official sources. Please verify independently before taking action.")
        
        if warnings:
            data['data_warnings'] = warnings
        
        return data
    
    @staticmethod
    def mark_as_verified(
        verification_source: str
    ) -> Dict[str, Any]:
        """
        Generate verification tracking data for marking data as verified
        
        Args:
            verification_source: Source used for verification
            
        Returns:
            Dictionary with verification tracking fields
        """
        return {
            'verification_status': VerificationStatus.VERIFIED,
            'verified_at': datetime.utcnow(),
            'verification_source': verification_source,
            'last_updated': datetime.utcnow()
        }
    
    @staticmethod
    def mark_as_unverified(
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate verification tracking data for marking data as unverified
        
        Args:
            source: Source attribution for unverified data
            
        Returns:
            Dictionary with verification tracking fields
        """
        return {
            'verification_status': VerificationStatus.UNVERIFIED,
            'verified_at': None,
            'verification_source': source,
            'last_updated': datetime.utcnow()
        }
    
    @staticmethod
    def should_reverify(
        verified_at: Optional[datetime],
        reverification_days: int = 30
    ) -> bool:
        """
        Check if data should be reverified based on age
        
        Args:
            verified_at: Timestamp of last verification
            reverification_days: Number of days before reverification needed
            
        Returns:
            True if reverification is needed, False otherwise
        """
        if not verified_at:
            return True
        
        age_days = VerificationTracker.calculate_data_age_days(verified_at)
        if age_days is None:
            return True
        
        return age_days >= reverification_days
