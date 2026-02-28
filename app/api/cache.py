"""Cache management API endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.services.offline_cache import CacheManager
from app.services.network_monitor import NetworkMonitor, OfflineModeHandler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["cache"])

# Initialize cache manager and network monitor
cache_manager = CacheManager()
network_monitor = NetworkMonitor()
offline_handler = OfflineModeHandler(cache_manager, network_monitor)


class CacheContentRequest(BaseModel):
    """Request to cache content"""
    content_type: str = Field(..., description="Type of content (schemes, health_tips, crop_advice, etc.)")
    content: Dict[str, Any] = Field(..., description="Content data to cache")
    priority: int = Field(default=3, ge=1, le=5, description="Priority level (1=critical, 5=nice-to-have)")
    language: str = Field(default="en", description="Language of content")
    ttl_hours: int = Field(default=168, description="Time to live in hours")


class CacheQueryRequest(BaseModel):
    """Request to query cached content"""
    content_type: str = Field(..., description="Type of content to retrieve")
    query: Optional[str] = Field(None, description="Optional search query")
    language: Optional[str] = Field(None, description="Optional language filter")


class SyncRequest(BaseModel):
    """Request to sync with server"""
    force: bool = Field(default=False, description="Force sync even if online")


@router.post("/content")
async def cache_content(request: CacheContentRequest):
    """
    Cache content for offline access
    
    Args:
        request: Cache content request
        
    Returns:
        Success status
    """
    try:
        success = cache_manager.cache_content(
            content_type=request.content_type,
            content=request.content,
            priority=request.priority,
            language=request.language,
            ttl_hours=request.ttl_hours
        )
        
        if success:
            return {
                "success": True,
                "message": "Content cached successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to cache content")
            
    except Exception as e:
        logger.error(f"Error caching content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_cache(request: CacheQueryRequest):
    """
    Query cached content
    
    Args:
        request: Cache query request
        
    Returns:
        List of cached content items
    """
    try:
        results = cache_manager.get_cached_content(
            content_type=request.content_type,
            query=request.query,
            language=request.language
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "from_cache": True
        }
        
    except Exception as e:
        logger.error(f"Error querying cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_cache(request: SyncRequest):
    """
    Sync cache with server
    
    Args:
        request: Sync request
        
    Returns:
        Sync result
    """
    try:
        # Check if online
        if not network_monitor.is_online() and not request.force:
            raise HTTPException(
                status_code=503,
                detail="Cannot sync while offline. Connect to internet and try again."
            )
        
        result = cache_manager.sync_with_server()
        
        return {
            "success": result.success,
            "synced_count": result.synced_count,
            "failed_count": result.failed_count,
            "errors": result.errors,
            "last_sync_time": result.last_sync_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invalidate")
async def invalidate_cache(
    content_type: Optional[str] = None,
    max_age_days: int = 7
):
    """
    Invalidate stale cached content
    
    Args:
        content_type: Optional content type to invalidate (None = all types)
        max_age_days: Maximum age in days before content is considered stale
        
    Returns:
        Number of items invalidated
    """
    try:
        count = cache_manager.invalidate_cache(
            content_type=content_type,
            max_age_days=max_age_days
        )
        
        return {
            "success": True,
            "invalidated_count": count,
            "message": f"Invalidated {count} stale cache items"
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        Cache statistics
    """
    try:
        stats = cache_manager.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connectivity")
async def check_connectivity():
    """
    Check network connectivity status
    
    Returns:
        Connectivity status
    """
    try:
        status = network_monitor.get_status()
        
        return {
            "is_online": status.is_online,
            "last_check": status.last_check,
            "last_online": status.last_online,
            "consecutive_failures": status.consecutive_failures
        }
        
    except Exception as e:
        logger.error(f"Error checking connectivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_monitoring():
    """
    Start network connectivity monitoring
    
    Returns:
        Success status
    """
    try:
        offline_handler.start_monitoring()
        
        return {
            "success": True,
            "message": "Network monitoring started"
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_monitoring():
    """
    Stop network connectivity monitoring
    
    Returns:
        Success status
    """
    try:
        offline_handler.stop_monitoring()
        
        return {
            "success": True,
            "message": "Network monitoring stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_cache():
    """
    Clear all cached content (for testing/debugging)
    
    Returns:
        Success status
    """
    try:
        success = cache_manager.clear_all_cache()
        
        if success:
            return {
                "success": True,
                "message": "Cache cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
            
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
