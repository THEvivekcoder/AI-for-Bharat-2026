"""Mandi Price Service for agricultural market prices"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.farmer import MandiPrice
from app.models.location import Location
from app.schemas.farmer import MandiPriceResponse, PriceTrendResponse
from datetime import datetime, timedelta, date
import math
import logging

logger = logging.getLogger(__name__)


class MandiPriceService:
    """Service for retrieving and managing mandi (market) prices"""
    
    def __init__(self, db: Session, cache=None):
        self.db = db
        self.cache = cache
    
    def get_current_price(
        self,
        crop_name: str,
        location: Location,
        radius_km: int = 50
    ) -> List[MandiPriceResponse]:
        """
        Get current mandi prices for a crop within specified radius
        
        Args:
            crop_name: Name of the crop
            location: User's location with coordinates
            radius_km: Search radius in kilometers (default 50km)
        
        Returns:
            List of mandi prices sorted by distance
        """
        logger.info(f"Fetching mandi prices for {crop_name} within {radius_km}km of {location.district}")
        
        # Check cache first
        cache_key = f"mandi_price:{crop_name}:{location.state}:{location.district}:{radius_km}"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached mandi prices")
                return cached_result
        
        # Get recent prices (within last 7 days)
        recent_date = date.today() - timedelta(days=7)
        
        # Query prices
        prices = self.db.query(MandiPrice).filter(
            and_(
                MandiPrice.crop_name == crop_name.lower(),
                MandiPrice.price_date >= recent_date
            )
        ).all()
        
        if not prices:
            logger.warning(f"No prices found for {crop_name}")
            return []
        
        # Calculate distances and filter by radius
        prices_with_distance = []
        for price in prices:
            if price.latitude and price.longitude and location.latitude and location.longitude:
                distance = self._calculate_distance(
                    location.latitude,
                    location.longitude,
                    price.latitude,
                    price.longitude
                )
                
                if distance <= radius_km:
                    prices_with_distance.append((price, distance))
            else:
                # If coordinates not available, include if same district
                if price.district == location.district:
                    prices_with_distance.append((price, 0))
        
        # Sort by distance
        prices_with_distance.sort(key=lambda x: x[1])
        
        # Get most recent price for each mandi
        mandi_latest_prices = {}
        for price, distance in prices_with_distance:
            mandi_key = f"{price.mandi_name}_{price.district}"
            if mandi_key not in mandi_latest_prices:
                mandi_latest_prices[mandi_key] = (price, distance)
            else:
                # Keep the most recent price
                existing_price, existing_distance = mandi_latest_prices[mandi_key]
                if price.price_date > existing_price.price_date:
                    mandi_latest_prices[mandi_key] = (price, distance)
        
        # Convert to response format
        result = []
        for price, distance in mandi_latest_prices.values():
            result.append(MandiPriceResponse(
                mandi_name=price.mandi_name,
                crop_name=price.crop_name,
                price_per_quintal=price.price_per_quintal,
                price_date=price.price_date,
                state=price.state,
                district=price.district,
                distance_km=round(distance, 2) if distance > 0 else None,
                source=price.source
            ))
        
        # Cache the result for 1 hour
        if self.cache:
            self.cache.setex(cache_key, 3600, result)
        
        logger.info(f"Found {len(result)} mandi prices")
        return result
    
    def get_price_trend(
        self,
        crop_name: str,
        location: Location,
        days: int = 30
    ) -> Optional[PriceTrendResponse]:
        """
        Get price trend for a crop over specified period
        
        Args:
            crop_name: Name of the crop
            location: User's location
            days: Number of days to look back (default 30)
        
        Returns:
            Price trend with historical data and statistics
        """
        logger.info(f"Fetching price trend for {crop_name} over {days} days")
        
        # Get prices from the specified period
        start_date = date.today() - timedelta(days=days)
        
        prices = self.db.query(MandiPrice).filter(
            and_(
                MandiPrice.crop_name == crop_name.lower(),
                MandiPrice.state == location.state,
                MandiPrice.price_date >= start_date
            )
        ).order_by(MandiPrice.price_date).all()
        
        if not prices:
            logger.warning(f"No price trend data found for {crop_name}")
            return None
        
        # Organize prices by date
        price_data = []
        all_prices = []
        
        for price in prices:
            price_data.append({
                "date": price.price_date.isoformat(),
                "price": price.price_per_quintal,
                "mandi_name": price.mandi_name
            })
            all_prices.append(price.price_per_quintal)
        
        # Calculate statistics
        avg_price = sum(all_prices) / len(all_prices)
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        # Determine trend
        if len(all_prices) >= 2:
            # Compare first half average with second half average
            mid_point = len(all_prices) // 2
            first_half_avg = sum(all_prices[:mid_point]) / mid_point
            second_half_avg = sum(all_prices[mid_point:]) / (len(all_prices) - mid_point)
            
            if second_half_avg > first_half_avg * 1.05:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return PriceTrendResponse(
            crop_name=crop_name,
            location=f"{location.district}, {location.state}",
            prices=price_data,
            average_price=round(avg_price, 2),
            min_price=round(min_price, 2),
            max_price=round(max_price, 2),
            trend=trend
        )
    
    def update_prices(self, prices_data: List[Dict[str, Any]]) -> int:
        """
        Update mandi prices from external API data
        
        Args:
            prices_data: List of price dictionaries from external API
        
        Returns:
            Number of prices updated
        """
        logger.info(f"Updating {len(prices_data)} mandi prices")
        
        count = 0
        for price_data in prices_data:
            try:
                # Check if price already exists
                existing = self.db.query(MandiPrice).filter(
                    and_(
                        MandiPrice.crop_name == price_data["crop_name"].lower(),
                        MandiPrice.mandi_name == price_data["mandi_name"],
                        MandiPrice.price_date == price_data["price_date"]
                    )
                ).first()
                
                if existing:
                    # Update existing price
                    existing.price_per_quintal = price_data["price_per_quintal"]
                    existing.source = price_data.get("source")
                else:
                    # Create new price entry
                    new_price = MandiPrice(
                        crop_name=price_data["crop_name"].lower(),
                        mandi_name=price_data["mandi_name"],
                        state=price_data["state"],
                        district=price_data["district"],
                        latitude=price_data.get("latitude"),
                        longitude=price_data.get("longitude"),
                        price_per_quintal=price_data["price_per_quintal"],
                        price_date=price_data["price_date"],
                        source=price_data.get("source")
                    )
                    self.db.add(new_price)
                
                count += 1
            except Exception as e:
                logger.error(f"Error updating price: {e}")
                continue
        
        self.db.commit()
        logger.info(f"Successfully updated {count} prices")
        
        # Clear cache after update
        if self.cache:
            # Clear all mandi price cache keys
            # In production, use a more sophisticated cache invalidation strategy
            pass
        
        return count
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First location coordinates
            lat2, lon2: Second location coordinates
        
        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def seed_sample_prices(self):
        """Seed database with sample mandi prices for testing"""
        logger.info("Seeding sample mandi prices")
        
        sample_prices = [
            {
                "crop_name": "rice",
                "mandi_name": "Delhi Mandi",
                "state": "Delhi",
                "district": "New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "price_per_quintal": 2500.0,
                "price_date": date.today(),
                "source": "Sample Data"
            },
            {
                "crop_name": "wheat",
                "mandi_name": "Delhi Mandi",
                "state": "Delhi",
                "district": "New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "price_per_quintal": 2200.0,
                "price_date": date.today(),
                "source": "Sample Data"
            },
            {
                "crop_name": "rice",
                "mandi_name": "Gurgaon Mandi",
                "state": "Haryana",
                "district": "Gurgaon",
                "latitude": 28.4595,
                "longitude": 77.0266,
                "price_per_quintal": 2450.0,
                "price_date": date.today(),
                "source": "Sample Data"
            },
            {
                "crop_name": "wheat",
                "mandi_name": "Gurgaon Mandi",
                "state": "Haryana",
                "district": "Gurgaon",
                "latitude": 28.4595,
                "longitude": 77.0266,
                "price_per_quintal": 2180.0,
                "price_date": date.today(),
                "source": "Sample Data"
            }
        ]
        
        return self.update_prices(sample_prices)
