"""
Mandi Price API Integration
Integrates with Agmarknet and other agricultural market price APIs
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging
from app.integrations.api_keys import api_keys

logger = logging.getLogger(__name__)


class MandiPriceAPI:
    """Client for mandi price APIs"""
    
    def __init__(self):
        # Agmarknet API endpoint
        self.base_url = "https://api.data.gov.in/resource"
        self.api_key = api_keys.agmarknet_key or api_keys.data_gov_in_key
        self.timeout = 30.0
        
    async def fetch_current_prices(
        self,
        crop: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        date_from: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch current mandi prices for a crop
        
        Args:
            crop: Crop name
            state: State filter (optional)
            district: District filter (optional)
            date_from: Fetch prices from this date onwards
            
        Returns:
            List of price records
        """
        if not self.api_key:
            logger.warning("Mandi price API key not configured")
            return []
        
        try:
            # Default to last 7 days if no date specified
            if not date_from:
                date_from = date.today() - timedelta(days=7)
            
            params = {
                "api-key": self.api_key,
                "format": "json",
                "filters[commodity]": crop,
                "filters[from_date]": date_from.strftime("%Y-%m-%d"),
                "limit": 1000
            }
            
            if state:
                params["filters[state]"] = state
            if district:
                params["filters[district]"] = district
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Note: Actual endpoint depends on specific Agmarknet dataset
                response = await client.get(
                    f"{self.base_url}/mandi-prices",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                prices = data.get("records", [])
                
                logger.info(f"Fetched {len(prices)} price records for {crop}")
                return prices
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching mandi prices: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching mandi prices: {e}")
            return []
    
    async def fetch_price_trend(
        self,
        crop: str,
        state: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch price trend for a crop over specified days
        
        Args:
            crop: Crop name
            state: State name
            days: Number of days to fetch
            
        Returns:
            List of price records with dates
        """
        date_from = date.today() - timedelta(days=days)
        return await self.fetch_current_prices(
            crop=crop,
            state=state,
            date_from=date_from
        )
    
    async def fetch_all_commodities(self) -> List[str]:
        """
        Fetch list of all available commodities
        
        Returns:
            List of commodity names
        """
        if not self.api_key:
            logger.warning("Mandi price API key not configured")
            return []
        
        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": 1000
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/commodities",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                records = data.get("records", [])
                
                commodities = [r.get("commodity") for r in records if r.get("commodity")]
                return list(set(commodities))  # Remove duplicates
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching commodities list: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching commodities: {e}")
            return []


# Singleton instance
mandi_price_api = MandiPriceAPI()
