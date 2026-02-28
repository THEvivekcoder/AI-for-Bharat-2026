# Offline Cache Manager Implementation

## Overview

The Offline Cache Manager provides robust offline functionality for BharatSahayak, enabling users in low-connectivity areas to access cached content and sync data when connectivity is restored.

## Components

### 1. CacheManager (`app/services/offline_cache.py`)

Manages local SQLite database for offline content storage.

**Key Features:**
- Priority-based caching (1=critical, 5=nice-to-have)
- Automatic cache eviction when size limits reached
- TTL-based expiration
- Content type categorization
- Pending sync queue for offline operations

**Database Schema:**

```sql
-- Cached content (generic)
CREATE TABLE cached_content (
    content_id TEXT PRIMARY KEY,
    content_type TEXT NOT NULL,
    data TEXT NOT NULL,
    language TEXT,
    priority INTEGER,
    cached_at INTEGER,
    expires_at INTEGER
)

-- Pending sync operations
CREATE TABLE pending_sync (
    sync_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_data TEXT NOT NULL,
    created_at INTEGER
)

-- User preferences (offline)
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    profile_data TEXT NOT NULL,
    updated_at INTEGER
)
```

**Methods:**

- `cache_content()` - Cache content with priority and TTL
- `get_cached_content()` - Retrieve cached content with optional filtering
- `sync_with_server()` - Sync pending operations with server
- `invalidate_cache()` - Remove stale content
- `get_cache_stats()` - Get cache statistics
- `add_pending_sync()` - Queue operation for later sync
- `get_pending_syncs()` - Get all pending operations

**Usage Example:**

```python
from app.services.offline_cache import CacheManager

# Initialize
cache = CacheManager(db_path="data/offline_cache.db", max_cache_size_mb=50)

# Cache content
cache.cache_content(
    content_type="schemes",
    content={"id": "scheme_001", "name": "PM-KISAN"},
    priority=1,  # Critical
    language="en",
    ttl_hours=168  # 7 days
)

# Retrieve cached content
results = cache.get_cached_content(
    content_type="schemes",
    query="farmer",
    language="en"
)

# Sync with server
result = cache.sync_with_server(sync_callback=my_sync_function)
```

### 2. NetworkMonitor (`app/services/network_monitor.py`)

Monitors network connectivity and detects online/offline transitions.

**Key Features:**
- Periodic connectivity checks
- Multiple DNS server fallback
- Callback system for connectivity changes
- Background monitoring thread
- Consecutive failure detection

**Methods:**

- `check_connectivity()` - Check if network is available
- `is_online()` - Get current connectivity status
- `get_status()` - Get detailed connectivity status
- `register_callback()` - Register callback for connectivity changes
- `start_monitoring()` - Start background monitoring
- `stop_monitoring()` - Stop background monitoring

**Usage Example:**

```python
from app.services.network_monitor import NetworkMonitor

# Initialize
monitor = NetworkMonitor(check_interval=30)

# Register callback
def on_connectivity_change(is_online: bool):
    if is_online:
        print("Back online!")
    else:
        print("Gone offline!")

monitor.register_callback(on_connectivity_change)

# Start monitoring
monitor.start_monitoring()

# Check status
if monitor.is_online():
    print("Connected")
```

### 3. OfflineModeHandler (`app/services/network_monitor.py`)

Handles automatic fallback to cached data and sync on reconnection.

**Key Features:**
- Automatic fallback to cache when offline
- Automatic sync trigger on reconnection
- Transparent data fetching with fallback

**Methods:**

- `is_offline()` - Check if in offline mode
- `get_data_with_fallback()` - Get data with automatic cache fallback
- `start_monitoring()` - Start connectivity monitoring
- `stop_monitoring()` - Stop connectivity monitoring

**Usage Example:**

```python
from app.services.offline_cache import CacheManager
from app.services.network_monitor import NetworkMonitor, OfflineModeHandler

# Initialize
cache = CacheManager()
monitor = NetworkMonitor()
handler = OfflineModeHandler(cache, monitor)

# Start monitoring
handler.start_monitoring()

# Get data with automatic fallback
def fetch_schemes():
    # Fetch from server
    return api.get_schemes()

data, from_cache = handler.get_data_with_fallback(
    fetch_func=fetch_schemes,
    content_type="schemes",
    language="en"
)

if from_cache:
    print("Using cached data (offline)")
else:
    print("Fetched from server (online)")
```

## API Endpoints

### Cache Management

**POST /api/cache/content** - Cache content for offline access

Request:
```json
{
  "content_type": "schemes",
  "content": {
    "id": "scheme_001",
    "name": "PM-KISAN"
  },
  "priority": 1,
  "language": "en",
  "ttl_hours": 168
}
```

Response:
```json
{
  "success": true,
  "message": "Content cached successfully"
}
```

**POST /api/cache/query** - Query cached content

Request:
```json
{
  "content_type": "schemes",
  "query": "farmer",
  "language": "en"
}
```

Response:
```json
{
  "success": true,
  "count": 5,
  "results": [...],
  "from_cache": true
}
```

**POST /api/cache/sync** - Sync cache with server

Request:
```json
{
  "force": false
}
```

Response:
```json
{
  "success": true,
  "synced_count": 3,
  "failed_count": 0,
  "errors": [],
  "last_sync_time": 1677209514
}
```

**GET /api/cache/stats** - Get cache statistics

Response:
```json
{
  "success": true,
  "stats": {
    "total_items": 150,
    "total_size_mb": 2.5,
    "max_size_mb": 50,
    "usage_percent": 5.0,
    "by_type": {
      "schemes": 50,
      "health_tips": 30,
      "crop_advice": 70
    },
    "by_priority": {
      "1": 20,
      "2": 50,
      "3": 80
    },
    "pending_syncs": 5
  }
}
```

**GET /api/cache/connectivity** - Check network connectivity

Response:
```json
{
  "is_online": true,
  "last_check": 1677209514,
  "last_online": 1677209514,
  "consecutive_failures": 0
}
```

**DELETE /api/cache/invalidate** - Invalidate stale cache

Query params: `content_type` (optional), `max_age_days` (default: 7)

Response:
```json
{
  "success": true,
  "invalidated_count": 10,
  "message": "Invalidated 10 stale cache items"
}
```

**DELETE /api/cache/clear** - Clear all cache

Response:
```json
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

### Monitoring

**POST /api/cache/monitoring/start** - Start network monitoring

Response:
```json
{
  "success": true,
  "message": "Network monitoring started"
}
```

**POST /api/cache/monitoring/stop** - Stop network monitoring

Response:
```json
{
  "success": true,
  "message": "Network monitoring stopped"
}
```

## Content Types

The system supports caching various content types:

- `schemes` - Government schemes
- `health_tips` - Health guidance and tips
- `crop_advice` - Agricultural recommendations
- `mandi_prices` - Market prices
- `skill_programs` - Skill development programs
- `job_postings` - Government job listings
- `health_facilities` - Health facility information
- `frequently_asked` - FAQ content

## Priority Levels

Content is cached with priority levels to manage limited storage:

1. **Priority 1 (Critical)** - Essential information (emergency health, critical schemes)
2. **Priority 2 (High)** - Important information (popular schemes, common queries)
3. **Priority 3 (Medium)** - Useful information (general health tips, crop advice)
4. **Priority 4 (Low)** - Nice-to-have (additional resources)
5. **Priority 5 (Optional)** - Supplementary content

When cache is full, lower priority items are evicted first.

## Cache Eviction Strategy

1. Check cache size before adding new content
2. If cache exceeds max size:
   - Evict items with priority >= new item's priority
   - Start with lowest priority items first
   - Evict oldest items within same priority
3. Expired items (past TTL) are automatically excluded from queries

## Sync Strategy

### Pending Operations

When offline, operations are queued for later sync:

```python
# Queue operation while offline
cache.add_pending_sync(
    operation="create",
    entity_type="user_profile",
    entity_data={"user_id": "123", "name": "John"}
)

# Sync when back online
result = cache.sync_with_server(sync_callback=my_sync_function)
```

### Sync Callback

Provide a callback function to handle actual server sync:

```python
def sync_callback(operation, entity_type, entity_data):
    """
    Handle sync with server
    
    Args:
        operation: create, update, or delete
        entity_type: Type of entity
        entity_data: Entity data
        
    Returns:
        True if synced successfully, False otherwise
    """
    try:
        if operation == "create":
            api.create(entity_type, entity_data)
        elif operation == "update":
            api.update(entity_type, entity_data)
        elif operation == "delete":
            api.delete(entity_type, entity_data)
        return True
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False

# Use callback
result = cache.sync_with_server(sync_callback=sync_callback)
```

## Testing

### Unit Tests

Run offline cache tests:

```bash
python scripts/test_offline_cache.py
```

### API Tests

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Run API tests:
```bash
python scripts/test_cache_endpoints.py
```

## Configuration

Configure cache settings in `app/config.py`:

```python
# Cache settings
CACHE_MAX_SIZE_MB = 50  # Maximum cache size
CACHE_DEFAULT_TTL_HOURS = 168  # 7 days
CACHE_DB_PATH = "data/offline_cache.db"

# Network monitoring
NETWORK_CHECK_INTERVAL = 30  # seconds
NETWORK_CHECK_TIMEOUT = 5  # seconds
```

## Best Practices

1. **Cache Critical Content First** - Use priority 1-2 for essential information
2. **Set Appropriate TTL** - Balance freshness vs. offline availability
3. **Monitor Cache Size** - Check stats regularly to avoid eviction
4. **Handle Offline Gracefully** - Always provide fallback to cached data
5. **Sync Regularly** - Trigger sync when connectivity restored
6. **Clear Stale Data** - Periodically invalidate old cache entries

## Error Handling

### Offline Mode Errors

When a feature requires internet but user is offline:

```json
{
  "error": "OFFLINE_FEATURE_UNAVAILABLE",
  "message": "This feature requires internet connection. Please connect and try again.",
  "offline_alternatives": ["View cached schemes", "Access saved content"],
  "last_sync_time": "2024-01-19T08:00:00Z"
}
```

### Cache Full Errors

When cache is full and cannot evict more items:

```json
{
  "error": "CACHE_FULL",
  "message": "Cache is full. Please clear some cached content.",
  "current_size_mb": 50,
  "max_size_mb": 50,
  "suggestions": ["Clear old cache", "Increase cache size"]
}
```

## Performance Considerations

- **SQLite Performance** - Indexed queries for fast retrieval
- **Memory Usage** - Lazy loading of cached content
- **Background Monitoring** - Non-blocking connectivity checks
- **Batch Operations** - Sync multiple operations together
- **Compression** - JSON data stored as text (consider compression for large datasets)

## Future Enhancements

1. **Differential Sync** - Only sync changed data
2. **Conflict Resolution** - Handle concurrent modifications
3. **Compression** - Compress cached data to save space
4. **Selective Sync** - User-configurable sync preferences
5. **Background Sync** - Automatic sync in background
6. **Cache Warming** - Pre-cache popular content
7. **Analytics** - Track cache hit/miss rates

## Requirements Validation

This implementation satisfies:

- **Requirement 7.1** - Offline access to cached content ✓
- **Requirement 7.3** - Priority-based caching ✓
- **Requirement 7.4** - Sync on reconnection ✓

## Related Documentation

- [Design Document](.kiro/specs/bharatsahayak/design.md)
- [Requirements Document](.kiro/specs/bharatsahayak/requirements.md)
- [API Documentation](../README.md)
