"""Offline Cache Manager for low-connectivity scenarios"""
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CachedContent:
    """Represents cached content"""
    content_id: str
    content_type: str
    data: Dict[str, Any]
    language: str
    priority: int
    cached_at: int
    expires_at: int


@dataclass
class SyncOperation:
    """Represents a pending sync operation"""
    sync_id: str
    operation: str  # create, update, delete
    entity_type: str
    entity_data: Dict[str, Any]
    created_at: int


@dataclass
class SyncResult:
    """Result of sync operation"""
    success: bool
    synced_count: int
    failed_count: int
    errors: List[str]
    last_sync_time: int


class CacheManager:
    """
    Manages offline cache using SQLite for low-connectivity scenarios
    
    Responsibilities:
    - Store content for offline access with priority handling
    - Retrieve cached content when offline
    - Sync with server when connectivity is restored
    - Manage cache invalidation and eviction
    """
    
    def __init__(self, db_path: str = "data/offline_cache.db", max_cache_size_mb: int = 50):
        """
        Initialize Cache Manager
        
        Args:
            db_path: Path to SQLite database file
            max_cache_size_mb: Maximum cache size in megabytes
        """
        self.db_path = db_path
        self.max_cache_size_mb = max_cache_size_mb
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"CacheManager initialized with db_path={db_path}, max_size={max_cache_size_mb}MB")
    
    def _init_database(self) -> None:
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cached schemes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_schemes (
                scheme_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                language TEXT,
                priority INTEGER,
                cached_at INTEGER,
                expires_at INTEGER
            )
        """)
        
        # Cached content table (generic)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_content (
                content_id TEXT PRIMARY KEY,
                content_type TEXT NOT NULL,
                data TEXT NOT NULL,
                language TEXT,
                priority INTEGER,
                cached_at INTEGER,
                expires_at INTEGER
            )
        """)
        
        # Pending sync operations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_sync (
                sync_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_data TEXT NOT NULL,
                created_at INTEGER
            )
        """)
        
        # User preferences (offline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                profile_data TEXT NOT NULL,
                updated_at INTEGER
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cached_content_type 
            ON cached_content(content_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cached_content_priority 
            ON cached_content(priority)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cached_content_expires 
            ON cached_content(expires_at)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("SQLite database schema initialized")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def cache_content(
        self, 
        content_type: str, 
        content: Dict[str, Any], 
        priority: int,
        language: str = "en",
        ttl_hours: int = 168  # 7 days default
    ) -> bool:
        """
        Cache content for offline access with priority handling
        
        Args:
            content_type: Type of content (schemes, health_tips, crop_advice, etc.)
            content: Content data to cache
            priority: Priority level (1=critical, 5=nice-to-have)
            language: Language of content
            ttl_hours: Time to live in hours
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            # Generate content ID
            content_id = f"{content_type}_{content.get('id', str(time.time()))}"
            
            # Calculate timestamps
            cached_at = int(time.time())
            expires_at = cached_at + (ttl_hours * 3600)
            
            # Check cache size and evict if necessary
            self._ensure_cache_space(priority)
            
            # Serialize content
            data_json = json.dumps(content)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert or replace content
            cursor.execute("""
                INSERT OR REPLACE INTO cached_content 
                (content_id, content_type, data, language, priority, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (content_id, content_type, data_json, language, priority, cached_at, expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cached content: type={content_type}, id={content_id}, priority={priority}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching content: {e}")
            return False
    
    def get_cached_content(
        self, 
        content_type: str, 
        query: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve content from local cache
        
        Args:
            content_type: Type of content to retrieve
            query: Optional search query (simple text matching)
            language: Optional language filter
            
        Returns:
            List of cached content items
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query
            sql = """
                SELECT data FROM cached_content 
                WHERE content_type = ? 
                AND expires_at > ?
            """
            params = [content_type, int(time.time())]
            
            if language:
                sql += " AND language = ?"
                params.append(language)
            
            sql += " ORDER BY priority ASC, cached_at DESC"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Deserialize and filter by query if provided
            results = []
            for row in rows:
                data = json.loads(row['data'])
                
                # Simple text search if query provided
                if query:
                    data_str = json.dumps(data).lower()
                    if query.lower() not in data_str:
                        continue
                
                results.append(data)
            
            logger.info(f"Retrieved {len(results)} cached items for type={content_type}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving cached content: {e}")
            return []
    
    def _ensure_cache_space(self, new_priority: int) -> None:
        """
        Ensure there's space in cache by evicting low-priority items if needed
        
        Args:
            new_priority: Priority of new content being added
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get current cache size
            cursor.execute("SELECT SUM(LENGTH(data)) as total_size FROM cached_content")
            row = cursor.fetchone()
            current_size = row['total_size'] or 0
            
            # If cache is full, evict low-priority items
            if current_size > self.max_cache_size_bytes:
                # Evict items with priority >= new_priority (lower priority)
                # Start with lowest priority first
                cursor.execute("""
                    DELETE FROM cached_content 
                    WHERE content_id IN (
                        SELECT content_id FROM cached_content 
                        WHERE priority >= ?
                        ORDER BY priority DESC, cached_at ASC
                        LIMIT 10
                    )
                """, (new_priority,))
                
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Evicted {deleted} low-priority items to make space")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring cache space: {e}")
    
    def invalidate_cache(self, content_type: Optional[str] = None, max_age_days: int = 7) -> int:
        """
        Remove stale cached content
        
        Args:
            content_type: Optional content type to invalidate (None = all types)
            max_age_days: Maximum age in days before content is considered stale
            
        Returns:
            Number of items invalidated
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff_time = int(time.time()) - (max_age_days * 86400)
            
            if content_type:
                cursor.execute("""
                    DELETE FROM cached_content 
                    WHERE content_type = ? AND (expires_at < ? OR cached_at < ?)
                """, (content_type, int(time.time()), cutoff_time))
            else:
                cursor.execute("""
                    DELETE FROM cached_content 
                    WHERE expires_at < ? OR cached_at < ?
                """, (int(time.time()), cutoff_time))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Invalidated {deleted} stale cache items")
            return deleted
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    def add_pending_sync(
        self, 
        operation: str, 
        entity_type: str, 
        entity_data: Dict[str, Any]
    ) -> str:
        """
        Add operation to pending sync queue
        
        Args:
            operation: Operation type (create, update, delete)
            entity_type: Type of entity
            entity_data: Entity data
            
        Returns:
            Sync operation ID
        """
        try:
            sync_id = f"{entity_type}_{operation}_{int(time.time())}"
            created_at = int(time.time())
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pending_sync (sync_id, operation, entity_type, entity_data, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (sync_id, operation, entity_type, json.dumps(entity_data), created_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added pending sync: {sync_id}")
            return sync_id
            
        except Exception as e:
            logger.error(f"Error adding pending sync: {e}")
            return ""
    
    def get_pending_syncs(self) -> List[SyncOperation]:
        """
        Get all pending sync operations
        
        Returns:
            List of pending sync operations
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM pending_sync ORDER BY created_at ASC")
            rows = cursor.fetchall()
            conn.close()
            
            operations = []
            for row in rows:
                operations.append(SyncOperation(
                    sync_id=row['sync_id'],
                    operation=row['operation'],
                    entity_type=row['entity_type'],
                    entity_data=json.loads(row['entity_data']),
                    created_at=row['created_at']
                ))
            
            return operations
            
        except Exception as e:
            logger.error(f"Error getting pending syncs: {e}")
            return []
    
    def clear_pending_sync(self, sync_id: str) -> bool:
        """
        Remove sync operation from queue after successful sync
        
        Args:
            sync_id: Sync operation ID
            
        Returns:
            True if cleared successfully
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM pending_sync WHERE sync_id = ?", (sync_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared pending sync: {sync_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing pending sync: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total items
            cursor.execute("SELECT COUNT(*) as count FROM cached_content")
            total_items = cursor.fetchone()['count']
            
            # Total size
            cursor.execute("SELECT SUM(LENGTH(data)) as size FROM cached_content")
            total_size = cursor.fetchone()['size'] or 0
            
            # Items by type
            cursor.execute("""
                SELECT content_type, COUNT(*) as count 
                FROM cached_content 
                GROUP BY content_type
            """)
            by_type = {row['content_type']: row['count'] for row in cursor.fetchall()}
            
            # Items by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM cached_content 
                GROUP BY priority
            """)
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            # Pending syncs
            cursor.execute("SELECT COUNT(*) as count FROM pending_sync")
            pending_syncs = cursor.fetchone()['count']
            
            conn.close()
            
            return {
                "total_items": total_items,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_size_mb": self.max_cache_size_mb,
                "usage_percent": round((total_size / self.max_cache_size_bytes) * 100, 2),
                "by_type": by_type,
                "by_priority": by_priority,
                "pending_syncs": pending_syncs
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def sync_with_server(self, sync_callback: Optional[callable] = None) -> SyncResult:
        """
        Synchronize local cache with server
        - Upload pending user data
        - Download updated content
        - Resolve conflicts
        
        Args:
            sync_callback: Optional callback function to handle actual sync with server
                          Should accept (operation, entity_type, entity_data) and return success bool
        
        Returns:
            SyncResult with status and changes
        """
        synced_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Get all pending sync operations
            pending_ops = self.get_pending_syncs()
            
            logger.info(f"Starting sync with {len(pending_ops)} pending operations")
            
            # Process each pending operation
            for op in pending_ops:
                try:
                    # If callback provided, use it to sync with server
                    if sync_callback:
                        success = sync_callback(op.operation, op.entity_type, op.entity_data)
                    else:
                        # Default behavior: just mark as synced (for testing)
                        success = True
                    
                    if success:
                        # Clear from pending queue
                        self.clear_pending_sync(op.sync_id)
                        synced_count += 1
                        logger.info(f"Synced operation: {op.sync_id}")
                    else:
                        failed_count += 1
                        errors.append(f"Failed to sync {op.sync_id}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Error syncing {op.sync_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update last sync time
            last_sync_time = int(time.time())
            
            result = SyncResult(
                success=(failed_count == 0),
                synced_count=synced_count,
                failed_count=failed_count,
                errors=errors,
                last_sync_time=last_sync_time
            )
            
            logger.info(f"Sync completed: synced={synced_count}, failed={failed_count}")
            return result
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return SyncResult(
                success=False,
                synced_count=synced_count,
                failed_count=failed_count,
                errors=errors + [str(e)],
                last_sync_time=int(time.time())
            )
    
    def clear_all_cache(self) -> bool:
        """
        Clear all cached content (for testing/debugging)
        
        Returns:
            True if cleared successfully
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cached_content")
            cursor.execute("DELETE FROM cached_schemes")
            cursor.execute("DELETE FROM pending_sync")
            
            conn.commit()
            conn.close()
            
            logger.info("Cleared all cache")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
