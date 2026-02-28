"""
Example: Integrating Offline Cache with Services

This example demonstrates how to integrate the offline cache manager
with existing services to provide automatic offline fallback.
"""

from app.services.offline_cache import CacheManager
from app.services.network_monitor import NetworkMonitor, OfflineModeHandler
from app.services.scheme_repository import SchemeRepository
from typing import List, Dict, Any


class OfflineAwareSchemeService:
    """
    Example: Scheme Service with offline cache integration
    
    This service automatically falls back to cached data when offline
    and caches fresh data when online.
    """
    
    def __init__(self, scheme_repo: SchemeRepository):
        self.scheme_repo = scheme_repo
        
        # Initialize offline components
        self.cache = CacheManager()
        self.monitor = NetworkMonitor()
        self.offline_handler = OfflineModeHandler(self.cache, self.monitor)
        
        # Start monitoring
        self.offline_handler.start_monitoring()
    
    def get_schemes(self, category: str = None, language: str = "en") -> tuple[List[Dict], bool]:
        """
        Get schemes with automatic offline fallback
        
        Returns:
            Tuple of (schemes, from_cache)
        """
        def fetch_from_server():
            # Fetch from database/API
            schemes = self.scheme_repo.get_all_schemes(category=category)
            return [scheme.dict() for scheme in schemes]
        
        # Use offline handler for automatic fallback
        schemes, from_cache = self.offline_handler.get_data_with_fallback(
            fetch_func=fetch_from_server,
            content_type="schemes",
            query=category,
            language=language
        )
        
        return schemes, from_cache
    
    def search_schemes(self, query: str, language: str = "en") -> tuple[List[Dict], bool]:
        """
        Search schemes with offline support
        
        Returns:
            Tuple of (schemes, from_cache)
        """
        def fetch_from_server():
            schemes = self.scheme_repo.search_schemes(query=query)
            return [scheme.dict() for scheme in schemes]
        
        schemes, from_cache = self.offline_handler.get_data_with_fallback(
            fetch_func=fetch_from_server,
            content_type="schemes",
            query=query,
            language=language
        )
        
        return schemes, from_cache
    
    def cache_popular_schemes(self, language: str = "en") -> int:
        """
        Pre-cache popular schemes for offline access
        
        Returns:
            Number of schemes cached
        """
        # Get popular schemes
        popular_schemes = self.scheme_repo.get_all_schemes()[:50]  # Top 50
        
        cached_count = 0
        for scheme in popular_schemes:
            success = self.cache.cache_content(
                content_type="schemes",
                content=scheme.dict(),
                priority=1,  # High priority for popular schemes
                language=language,
                ttl_hours=168  # 7 days
            )
            if success:
                cached_count += 1
        
        return cached_count


class OfflineAwareFarmerService:
    """
    Example: Farmer Advisory Service with offline cache integration
    """
    
    def __init__(self, crop_advisor, mandi_service):
        self.crop_advisor = crop_advisor
        self.mandi_service = mandi_service
        
        # Initialize offline components
        self.cache = CacheManager()
        self.monitor = NetworkMonitor()
        self.offline_handler = OfflineModeHandler(self.cache, self.monitor)
        self.offline_handler.start_monitoring()
    
    def get_crop_recommendations(
        self, 
        farm_profile: Dict, 
        language: str = "en"
    ) -> tuple[List[Dict], bool]:
        """
        Get crop recommendations with offline fallback
        """
        def fetch_from_server():
            recommendations = self.crop_advisor.recommend_crops(farm_profile)
            return [rec.dict() for rec in recommendations]
        
        recs, from_cache = self.offline_handler.get_data_with_fallback(
            fetch_func=fetch_from_server,
            content_type="crop_advice",
            language=language
        )
        
        return recs, from_cache
    
    def get_mandi_prices(
        self, 
        crop: str, 
        location: str, 
        language: str = "en"
    ) -> tuple[List[Dict], bool]:
        """
        Get mandi prices with offline fallback
        
        Note: Prices are time-sensitive, so we use shorter TTL
        """
        def fetch_from_server():
            prices = self.mandi_service.get_current_price(crop, location)
            return [price.dict() for price in prices]
        
        # For time-sensitive data, check if cached data is recent
        if self.offline_handler.is_offline():
            # Use cached data but warn user it may be outdated
            cached_prices = self.cache.get_cached_content(
                content_type="mandi_prices",
                query=crop,
                language=language
            )
            return cached_prices, True
        
        # Online: fetch fresh data and cache it
        try:
            prices = fetch_from_server()
            
            # Cache with shorter TTL for time-sensitive data
            for price in prices:
                self.cache.cache_content(
                    content_type="mandi_prices",
                    content=price,
                    priority=2,
                    language=language,
                    ttl_hours=24  # Only 1 day for prices
                )
            
            return prices, False
            
        except Exception:
            # Fallback to cache on error
            cached_prices = self.cache.get_cached_content(
                content_type="mandi_prices",
                query=crop,
                language=language
            )
            return cached_prices, True


class OfflineAwareHealthService:
    """
    Example: Health Service with offline cache integration
    """
    
    def __init__(self, health_advisor):
        self.health_advisor = health_advisor
        
        # Initialize offline components
        self.cache = CacheManager()
        self.monitor = NetworkMonitor()
        self.offline_handler = OfflineModeHandler(self.cache, self.monitor)
        self.offline_handler.start_monitoring()
    
    def get_health_facilities(
        self, 
        location: Dict, 
        facility_type: str = None,
        language: str = "en"
    ) -> tuple[List[Dict], bool]:
        """
        Get health facilities with offline fallback
        """
        def fetch_from_server():
            facilities = self.health_advisor.find_facilities(
                location=location,
                facility_type=facility_type
            )
            return [facility.dict() for facility in facilities]
        
        facilities, from_cache = self.offline_handler.get_data_with_fallback(
            fetch_func=fetch_from_server,
            content_type="health_facilities",
            query=facility_type,
            language=language
        )
        
        return facilities, from_cache
    
    def cache_health_tips(self, language: str = "en") -> int:
        """
        Pre-cache common health tips for offline access
        """
        common_tips = [
            {
                "id": "tip_001",
                "title": "Hand Washing",
                "content": "Wash hands with soap for 20 seconds",
                "category": "hygiene"
            },
            {
                "id": "tip_002",
                "title": "Hydration",
                "content": "Drink 8 glasses of water daily",
                "category": "nutrition"
            },
            # Add more tips...
        ]
        
        cached_count = 0
        for tip in common_tips:
            success = self.cache.cache_content(
                content_type="health_tips",
                content=tip,
                priority=1,  # High priority for health tips
                language=language,
                ttl_hours=720  # 30 days (static content)
            )
            if success:
                cached_count += 1
        
        return cached_count


# Example usage in API endpoint
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Initialize services
# scheme_service = OfflineAwareSchemeService(scheme_repo)
# farmer_service = OfflineAwareFarmerService(crop_advisor, mandi_service)
# health_service = OfflineAwareHealthService(health_advisor)


@router.get("/api/schemes")
async def get_schemes(category: str = None, language: str = "en"):
    """
    Get schemes with automatic offline fallback
    """
    try:
        schemes, from_cache = scheme_service.get_schemes(category, language)
        
        return {
            "success": True,
            "schemes": schemes,
            "from_cache": from_cache,
            "offline_mode": from_cache,
            "message": "Using cached data (offline)" if from_cache else "Fresh data from server"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/farmer/market-price")
async def get_mandi_prices(crop: str, location: str, language: str = "en"):
    """
    Get mandi prices with offline fallback and freshness warning
    """
    try:
        prices, from_cache = farmer_service.get_mandi_prices(crop, location, language)
        
        response = {
            "success": True,
            "prices": prices,
            "from_cache": from_cache
        }
        
        if from_cache:
            response["warning"] = "Prices may be outdated. Connect to internet for latest prices."
            response["message"] = "Using cached prices (offline mode)"
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cache/warmup")
async def warmup_cache(language: str = "en"):
    """
    Pre-cache popular content for offline access
    """
    try:
        schemes_cached = scheme_service.cache_popular_schemes(language)
        health_tips_cached = health_service.cache_health_tips(language)
        
        return {
            "success": True,
            "message": "Cache warmed up successfully",
            "cached": {
                "schemes": schemes_cached,
                "health_tips": health_tips_cached
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Best Practices for Offline Integration:

"""
1. Always use OfflineModeHandler for automatic fallback
2. Cache fresh data when online for future offline use
3. Use appropriate priority levels (1=critical, 5=optional)
4. Set TTL based on data freshness requirements:
   - Static content (health tips): 30 days
   - Semi-static (schemes): 7 days
   - Dynamic (prices): 1 day
5. Provide clear feedback to users when using cached data
6. Warn users when cached data may be outdated
7. Pre-cache popular content during idle time
8. Monitor cache size and evict stale data regularly
9. Handle sync errors gracefully
10. Test offline scenarios thoroughly
"""
