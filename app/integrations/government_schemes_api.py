"""
Government Schemes API Integration
Integrates with data.gov.in and other government portals for scheme information
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from app.integrations.api_keys import api_keys

logger = logging.getLogger(__name__)


class GovernmentSchemesAPI:
    """Client for government schemes APIs"""
    
    def __init__(self):
        self.base_url = "https://api.data.gov.in/resource"
        self.api_key = api_keys.data_gov_in_key
        self.timeout = 30.0
        
    async def fetch_schemes(
        self,
        category: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch government schemes from data.gov.in API
        
        Args:
            category: Scheme category filter
            state: State filter
            limit: Maximum number of schemes to fetch
            
        Returns:
            List of scheme dictionaries
        """
        if not self.api_key:
            logger.warning("data.gov.in API key not configured")
            return []
        
        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            if category:
                params["filters[category]"] = category
            if state:
                params["filters[state]"] = state
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Note: This is a placeholder URL - actual endpoint depends on specific dataset
                response = await client.get(
                    f"{self.base_url}/schemes",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                schemes = data.get("records", [])
                
                logger.info(f"Fetched {len(schemes)} schemes from data.gov.in")
                return schemes
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching schemes from data.gov.in: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching schemes: {e}")
            return []
    
    async def fetch_scheme_details(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific scheme
        
        Args:
            scheme_id: Unique scheme identifier
            
        Returns:
            Scheme details dictionary or None
        """
        if not self.api_key:
            logger.warning("data.gov.in API key not configured")
            return None
        
        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "filters[id]": scheme_id
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/schemes",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                records = data.get("records", [])
                
                if records:
                    return records[0]
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching scheme details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching scheme details: {e}")
            return None
    
    async def verify_scheme_exists(self, scheme_name: str) -> bool:
        """
        Verify if a scheme exists in the government database
        
        Args:
            scheme_name: Name of the scheme to verify
            
        Returns:
            True if scheme exists, False otherwise
        """
        schemes = await self.fetch_schemes(limit=1000)
        
        for scheme in schemes:
            if scheme.get("name", "").lower() == scheme_name.lower():
                return True
        
        return False


# Singleton instance
government_schemes_api = GovernmentSchemesAPI()
