"""Service for integrating with AGMARKNET API via data.gov.in.

This service fetches real-time mandi prices from the Indian government's
AGMARKNET portal through the data.gov.in API.

API Documentation: https://data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgmarknetPrice:
    """Raw price data from AGMARKNET API."""
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    arrival_date: str
    min_price: float
    max_price: float
    modal_price: float


class AgmarknetService:
    """Service for fetching mandi prices from AGMARKNET API."""
    
    # Data.gov.in API endpoint for AGMARKNET data
    BASE_URL = "https://api.data.gov.in/resource"
    RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AGMARKNET service.
        
        Args:
            api_key: Optional API key for data.gov.in (not required for public access)
        """
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'BharatSahayak/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 100
    ) -> List[AgmarknetPrice]:
        """
        Fetch mandi prices from AGMARKNET API.
        
        Args:
            commodity: Commodity name (e.g., "Wheat", "Rice", "Cotton")
            state: Optional state filter
            district: Optional district filter
            limit: Maximum number of results (default 100)
            
        Returns:
            List of AgmarknetPrice objects
            
        Raises:
            requests.RequestException: If API request fails
        """
        try:
            # Build API URL
            url = f"{self.BASE_URL}/{self.RESOURCE_ID}"
            
            # Build query parameters
            params = {
                'api-key': self.api_key or '',
                'format': 'json',
                'limit': limit,
                'offset': 0
            }
            
            # Add filters
            filters = {}
            if commodity:
                filters['commodity'] = commodity.title()
            if state:
                filters['state'] = state.title()
            if district:
                filters['district'] = district.title()
            
            if filters:
                params['filters'] = filters
            
            logger.info(f"Fetching prices from AGMARKNET: commodity={commodity}, state={state}, district={district}")
            
            # Make API request
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract records
            records = data.get('records', [])
            
            if not records:
                logger.warning(f"No records found for commodity={commodity}, state={state}, district={district}")
                return []
            
            # Parse records into AgmarknetPrice objects
            prices = []
            for record in records:
                try:
                    price = self._parse_record(record)
                    if price:
                        prices.append(price)
                except Exception as e:
                    logger.warning(f"Failed to parse record: {e}")
                    continue
            
            logger.info(f"Fetched {len(prices)} prices from AGMARKNET")
            return prices
            
        except requests.RequestException as e:
            logger.error(f"AGMARKNET API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching prices: {e}")
            raise
    
    def _parse_record(self, record: Dict[str, Any]) -> Optional[AgmarknetPrice]:
        """
        Parse a single record from AGMARKNET API response.
        
        Args:
            record: Raw record from API
            
        Returns:
            AgmarknetPrice object or None if parsing fails
        """
        try:
            # Extract fields (field names may vary)
            state = record.get('state', '')
            district = record.get('district', '')
            market = record.get('market', '')
            commodity = record.get('commodity', '')
            variety = record.get('variety', '')
            arrival_date = record.get('arrival_date', '')
            
            # Parse prices (handle different formats)
            min_price = self._parse_price(record.get('min_price', 0))
            max_price = self._parse_price(record.get('max_price', 0))
            modal_price = self._parse_price(record.get('modal_price', 0))
            
            # Validate required fields
            if not all([state, district, market, commodity]):
                return None
            
            return AgmarknetPrice(
                state=state,
                district=district,
                market=market,
                commodity=commodity,
                variety=variety,
                arrival_date=arrival_date,
                min_price=min_price,
                max_price=max_price,
                modal_price=modal_price
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse record: {e}")
            return None
    
    def _parse_price(self, price_value: Any) -> float:
        """
        Parse price value from various formats.
        
        Args:
            price_value: Price value (string, int, or float)
            
        Returns:
            Float price value
        """
        try:
            if isinstance(price_value, (int, float)):
                return float(price_value)
            
            if isinstance(price_value, str):
                # Remove commas and convert to float
                price_str = price_value.replace(',', '').strip()
                return float(price_str) if price_str else 0.0
            
            return 0.0
            
        except (ValueError, TypeError):
            return 0.0
    
    def get_commodity_mapping(self, crop_name: str) -> str:
        """
        Map common crop names to AGMARKNET commodity names.
        
        Args:
            crop_name: Common crop name
            
        Returns:
            AGMARKNET commodity name
        """
        # Mapping of common names to AGMARKNET names
        mapping = {
            'wheat': 'Wheat',
            'rice': 'Rice',
            'paddy': 'Paddy(Dhan)(Common)',
            'soybean': 'Soyabean',
            'cotton': 'Cotton',
            'maize': 'Maize',
            'bajra': 'Bajra(Pearl Millet/Cumbu)',
            'jowar': 'Jowar(Sorghum)',
            'groundnut': 'Groundnut',
            'mustard': 'Mustard',
            'onion': 'Onion',
            'potato': 'Potato',
            'tomato': 'Tomato',
            'chilli': 'Chilli Red',
            'turmeric': 'Turmeric',
            'coriander': 'Coriander(Leaves)',
        }
        
        # Return mapped name or title case of input
        return mapping.get(crop_name.lower(), crop_name.title())
