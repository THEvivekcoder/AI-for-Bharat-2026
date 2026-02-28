"""Redis client configuration"""
import redis
from typing import Optional
from app.config import get_settings

settings = get_settings()

# Create Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    decode_responses=True
)


def get_redis() -> redis.Redis:
    """
    Get Redis client instance
    
    Returns:
        Redis client
    """
    return redis.Redis(connection_pool=redis_pool)


class RedisCache:
    """Redis cache wrapper with common operations"""
    
    def __init__(self):
        self.client = get_redis()
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        return self.client.get(key)
    
    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration in seconds"""
        return self.client.set(key, value, ex=expire)
    
    def delete(self, key: str) -> int:
        """Delete key"""
        return self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.client.exists(key) > 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        return self.client.expire(key, seconds)
