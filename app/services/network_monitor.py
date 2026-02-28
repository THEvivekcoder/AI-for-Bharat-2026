"""Network connectivity monitoring and offline mode detection"""
import socket
import logging
import time
from typing import Optional, Callable, List
from threading import Thread, Event
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConnectivityStatus:
    """Network connectivity status"""
    is_online: bool
    last_check: int
    last_online: Optional[int]
    consecutive_failures: int


class NetworkMonitor:
    """
    Monitor network connectivity and detect offline mode
    
    Responsibilities:
    - Check network connectivity periodically
    - Detect when device goes offline/online
    - Trigger callbacks on connectivity changes
    - Provide current connectivity status
    """
    
    def __init__(
        self, 
        check_interval: int = 30,
        check_hosts: Optional[List[str]] = None,
        timeout: int = 5
    ):
        """
        Initialize Network Monitor
        
        Args:
            check_interval: Seconds between connectivity checks
            check_hosts: List of hosts to check (default: common DNS servers)
            timeout: Timeout for connectivity check in seconds
        """
        self.check_interval = check_interval
        self.check_hosts = check_hosts or [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "208.67.222.222"  # OpenDNS
        ]
        self.timeout = timeout
        
        self.status = ConnectivityStatus(
            is_online=True,
            last_check=int(time.time()),
            last_online=int(time.time()),
            consecutive_failures=0
        )
        
        self._monitoring = False
        self._monitor_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._callbacks: List[Callable[[bool], None]] = []
        
        logger.info(f"NetworkMonitor initialized with interval={check_interval}s")
    
    def check_connectivity(self) -> bool:
        """
        Check if network is available by attempting to connect to known hosts
        
        Returns:
            True if online, False if offline
        """
        for host in self.check_hosts:
            try:
                # Try to create a socket connection
                socket.create_connection((host, 53), timeout=self.timeout)
                return True
            except (socket.timeout, socket.error, OSError):
                continue
        
        return False
    
    def is_online(self) -> bool:
        """
        Get current connectivity status
        
        Returns:
            True if online, False if offline
        """
        return self.status.is_online
    
    def get_status(self) -> ConnectivityStatus:
        """
        Get detailed connectivity status
        
        Returns:
            ConnectivityStatus object
        """
        return self.status
    
    def register_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Register callback to be called on connectivity changes
        
        Args:
            callback: Function that accepts bool (is_online) parameter
        """
        self._callbacks.append(callback)
        logger.info(f"Registered connectivity callback: {callback.__name__}")
    
    def start_monitoring(self) -> None:
        """Start background monitoring of network connectivity"""
        if self._monitoring:
            logger.warning("Monitoring already started")
            return
        
        self._monitoring = True
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Started network monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Stopped network monitoring")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self._monitoring and not self._stop_event.is_set():
            try:
                # Check connectivity
                is_online = self.check_connectivity()
                current_time = int(time.time())
                
                # Update status
                previous_status = self.status.is_online
                self.status.last_check = current_time
                
                if is_online:
                    self.status.is_online = True
                    self.status.last_online = current_time
                    self.status.consecutive_failures = 0
                else:
                    self.status.consecutive_failures += 1
                    # Only mark as offline after 2 consecutive failures
                    if self.status.consecutive_failures >= 2:
                        self.status.is_online = False
                
                # Trigger callbacks if status changed
                if previous_status != self.status.is_online:
                    logger.info(f"Connectivity changed: {'online' if self.status.is_online else 'offline'}")
                    self._trigger_callbacks(self.status.is_online)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next check
            self._stop_event.wait(self.check_interval)
    
    def _trigger_callbacks(self, is_online: bool) -> None:
        """Trigger all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(is_online)
            except Exception as e:
                logger.error(f"Error in connectivity callback: {e}")


class OfflineModeHandler:
    """
    Handle offline mode fallback and automatic sync on reconnection
    
    Responsibilities:
    - Detect offline mode
    - Provide fallback to cached data
    - Trigger sync when connectivity restored
    """
    
    def __init__(self, cache_manager, network_monitor: Optional[NetworkMonitor] = None):
        """
        Initialize Offline Mode Handler
        
        Args:
            cache_manager: CacheManager instance for offline data
            network_monitor: Optional NetworkMonitor instance
        """
        self.cache_manager = cache_manager
        self.network_monitor = network_monitor or NetworkMonitor()
        
        # Register callback for connectivity changes
        self.network_monitor.register_callback(self._on_connectivity_change)
        
        logger.info("OfflineModeHandler initialized")
    
    def is_offline(self) -> bool:
        """
        Check if currently in offline mode
        
        Returns:
            True if offline, False if online
        """
        return not self.network_monitor.is_online()
    
    def get_data_with_fallback(
        self, 
        fetch_func: Callable[[], any],
        content_type: str,
        query: Optional[str] = None,
        language: Optional[str] = None
    ) -> tuple[any, bool]:
        """
        Get data with automatic fallback to cache if offline
        
        Args:
            fetch_func: Function to fetch data from server
            content_type: Type of content for cache lookup
            query: Optional query for cache filtering
            language: Optional language for cache filtering
            
        Returns:
            Tuple of (data, from_cache)
        """
        # Try to fetch from server if online
        if self.network_monitor.is_online():
            try:
                data = fetch_func()
                
                # Cache the data for offline use
                if data:
                    if isinstance(data, list):
                        for item in data:
                            self.cache_manager.cache_content(
                                content_type=content_type,
                                content=item,
                                priority=2,  # Medium priority
                                language=language or "en"
                            )
                    else:
                        self.cache_manager.cache_content(
                            content_type=content_type,
                            content=data,
                            priority=2,
                            language=language or "en"
                        )
                
                return data, False
                
            except Exception as e:
                logger.warning(f"Failed to fetch from server, falling back to cache: {e}")
        
        # Fallback to cache
        cached_data = self.cache_manager.get_cached_content(
            content_type=content_type,
            query=query,
            language=language
        )
        
        logger.info(f"Using cached data: {len(cached_data)} items")
        return cached_data, True
    
    def _on_connectivity_change(self, is_online: bool) -> None:
        """
        Handle connectivity changes
        
        Args:
            is_online: True if now online, False if now offline
        """
        if is_online:
            logger.info("Connectivity restored, triggering sync")
            self._trigger_sync()
        else:
            logger.info("Connectivity lost, entering offline mode")
    
    def _trigger_sync(self) -> None:
        """Trigger sync with server when connectivity is restored"""
        try:
            result = self.cache_manager.sync_with_server()
            
            if result.success:
                logger.info(f"Sync successful: {result.synced_count} operations synced")
            else:
                logger.warning(f"Sync completed with errors: {result.failed_count} failed")
                
        except Exception as e:
            logger.error(f"Error triggering sync: {e}")
    
    def start_monitoring(self) -> None:
        """Start monitoring network connectivity"""
        self.network_monitor.start_monitoring()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring network connectivity"""
        self.network_monitor.stop_monitoring()
