"""Data models for offline caching functionality."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class CacheMetadata:
    """Metadata for cached content."""
    version: str
    timestamp: datetime
    content_type: str
    priority: int  # 1 (critical) to 5 (nice-to-have)
    size_bytes: int
    checksum: str


@dataclass
class CachedScheme:
    """Simplified scheme data for offline cache."""
    scheme_id: str
    name: str
    category: str
    description: str
    benefits: List[str]
    eligibility_summary: str
    required_documents: List[str]
    application_process: List[str]
    priority: int


@dataclass
class CacheExportResult:
    """Result of cache export operation."""
    success: bool
    file_key: str
    file_size: int
    schemes_count: int
    version: str
    timestamp: datetime
    s3_url: str
    error: Optional[str] = None


@dataclass
class CacheSyncRequest:
    """Request for cache synchronization."""
    last_sync_timestamp: Optional[datetime]
    categories: Optional[List[str]]
    max_size_kb: int = 100


@dataclass
class CacheSyncResponse:
    """Response for cache synchronization."""
    updated_schemes: List[str]
    deleted_schemes: List[str]
    total_size_kb: float
    sync_timestamp: datetime
    incremental: bool
