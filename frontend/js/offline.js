// Offline mode management
import { API } from './api.js';

let syncInProgress = false;
let lastSyncTime = null;
let offlineQueue = [];

export function initOffline(app) {
  console.log('Initializing offline mode...');
  
  // Load last sync time from localStorage
  lastSyncTime = localStorage.getItem('lastSyncTime');
  
  // Load offline queue from localStorage
  loadOfflineQueue();
  
  // Setup sync status indicator
  setupSyncIndicator();
  
  // Monitor network status
  monitorNetworkStatus(app);
  
  // Setup periodic sync check
  setupPeriodicSync();
  
  console.log('Offline mode initialized');
}

function setupSyncIndicator() {
  // Create sync status element if it doesn't exist
  const header = document.querySelector('.header-actions');
  
  if (!document.getElementById('syncIndicator')) {
    const syncIndicator = document.createElement('div');
    syncIndicator.id = 'syncIndicator';
    syncIndicator.className = 'sync-indicator hidden';
    syncIndicator.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
      </svg>
      <span id="syncStatus">Syncing...</span>
    `;
    header.insertBefore(syncIndicator, header.firstChild);
  }
}

function monitorNetworkStatus(app) {
  // Initial check
  updateNetworkStatus(app);
  
  // Listen for online/offline events
  window.addEventListener('online', () => {
    console.log('Network: Online');
    updateNetworkStatus(app);
    syncOfflineData(app);
  });
  
  window.addEventListener('offline', () => {
    console.log('Network: Offline');
    updateNetworkStatus(app);
  });
  
  // Periodic connectivity check
  setInterval(() => {
    checkConnectivity(app);
  }, 30000); // Check every 30 seconds
}

function updateNetworkStatus(app) {
  const isOnline = navigator.onLine;
  const offlineIndicator = document.getElementById('offlineIndicator');
  
  if (offlineIndicator) {
    if (isOnline) {
      offlineIndicator.classList.add('hidden');
    } else {
      offlineIndicator.classList.remove('hidden');
    }
  }
  
  // Update app state
  if (app) {
    app.isOnline = isOnline;
  }
}

async function checkConnectivity(app) {
  try {
    // Try to fetch a small resource to verify connectivity
    const response = await fetch('/api/health', {
      method: 'HEAD',
      cache: 'no-cache'
    });
    
    if (response.ok && !navigator.onLine) {
      // Browser thinks we're offline but we can reach the server
      console.log('Connectivity restored');
      window.dispatchEvent(new Event('online'));
    }
  } catch (error) {
    if (navigator.onLine) {
      // Browser thinks we're online but we can't reach the server
      console.log('Connectivity lost');
      window.dispatchEvent(new Event('offline'));
    }
  }
}

async function syncOfflineData(app) {
  if (syncInProgress) {
    console.log('Sync already in progress');
    return;
  }
  
  if (!navigator.onLine) {
    console.log('Cannot sync: offline');
    return;
  }
  
  if (offlineQueue.length === 0) {
    console.log('Nothing to sync');
    return;
  }
  
  console.log('Starting offline data sync...');
  syncInProgress = true;
  showSyncIndicator(true);
  
  try {
    // Process offline queue
    const results = await processOfflineQueue();
    
    console.log('Sync completed:', results);
    
    // Update last sync time
    lastSyncTime = new Date().toISOString();
    localStorage.setItem('lastSyncTime', lastSyncTime);
    
    // Show success notification
    showSyncNotification('Data synced successfully', 'success');
    
  } catch (error) {
    console.error('Sync failed:', error);
    showSyncNotification('Sync failed. Will retry later.', 'error');
  } finally {
    syncInProgress = false;
    showSyncIndicator(false);
  }
}

async function processOfflineQueue() {
  const results = {
    success: 0,
    failed: 0,
    errors: []
  };
  
  // Process each queued item
  for (let i = 0; i < offlineQueue.length; i++) {
    const item = offlineQueue[i];
    
    try {
      await processQueueItem(item);
      results.success++;
      
      // Remove from queue
      offlineQueue.splice(i, 1);
      i--;
      
    } catch (error) {
      console.error('Failed to process queue item:', error);
      results.failed++;
      results.errors.push({
        item,
        error: error.message
      });
    }
  }
  
  // Save updated queue
  saveOfflineQueue();
  
  return results;
}

async function processQueueItem(item) {
  const { type, data, timestamp } = item;
  
  switch (type) {
    case 'message':
      await API.sendMessage(data.message, data.sessionId, data.language);
      break;
      
    case 'event':
      await API.recordEvent(data.eventType, data.eventData);
      break;
      
    case 'profile_update':
      await API.updateUserProfile(data.profileData);
      break;
      
    default:
      console.warn('Unknown queue item type:', type);
  }
}

function showSyncIndicator(show) {
  const syncIndicator = document.getElementById('syncIndicator');
  
  if (syncIndicator) {
    if (show) {
      syncIndicator.classList.remove('hidden');
      // Add spinning animation
      const svg = syncIndicator.querySelector('svg');
      if (svg) {
        svg.style.animation = 'spin 1s linear infinite';
      }
    } else {
      syncIndicator.classList.add('hidden');
      const svg = syncIndicator.querySelector('svg');
      if (svg) {
        svg.style.animation = '';
      }
    }
  }
}

function showSyncNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `sync-notification ${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => {
    notification.classList.add('show');
  }, 100);
  
  // Hide and remove after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

export function queueOfflineAction(type, data) {
  const item = {
    id: Date.now() + Math.random(),
    type,
    data,
    timestamp: new Date().toISOString()
  };
  
  offlineQueue.push(item);
  saveOfflineQueue();
  
  console.log('Queued offline action:', type);
}

function loadOfflineQueue() {
  try {
    const stored = localStorage.getItem('offlineQueue');
    if (stored) {
      offlineQueue = JSON.parse(stored);
      console.log('Loaded offline queue:', offlineQueue.length, 'items');
    }
  } catch (error) {
    console.error('Failed to load offline queue:', error);
    offlineQueue = [];
  }
}

function saveOfflineQueue() {
  try {
    localStorage.setItem('offlineQueue', JSON.stringify(offlineQueue));
  } catch (error) {
    console.error('Failed to save offline queue:', error);
  }
}

function setupPeriodicSync() {
  // Try to sync every 5 minutes when online
  setInterval(() => {
    if (navigator.onLine && offlineQueue.length > 0) {
      syncOfflineData();
    }
  }, 5 * 60 * 1000);
}

export function getOfflineQueueStatus() {
  return {
    queueLength: offlineQueue.length,
    lastSyncTime,
    syncInProgress
  };
}

export function clearOfflineQueue() {
  offlineQueue = [];
  saveOfflineQueue();
  console.log('Offline queue cleared');
}

// Cache management
export async function cacheEssentialData() {
  if (!navigator.onLine) {
    console.log('Cannot cache: offline');
    return;
  }
  
  console.log('Caching essential data...');
  
  try {
    // Cache schemes
    const schemes = await API.getSchemes();
    localStorage.setItem('cached_schemes', JSON.stringify({
      data: schemes,
      timestamp: Date.now()
    }));
    
    // Cache languages
    const languages = await API.getSupportedLanguages();
    localStorage.setItem('cached_languages', JSON.stringify({
      data: languages,
      timestamp: Date.now()
    }));
    
    console.log('Essential data cached');
    
  } catch (error) {
    console.error('Failed to cache data:', error);
  }
}

export function getCachedData(key) {
  try {
    const stored = localStorage.getItem(`cached_${key}`);
    if (stored) {
      const { data, timestamp } = JSON.parse(stored);
      
      // Check if cache is still valid (24 hours)
      const age = Date.now() - timestamp;
      const maxAge = 24 * 60 * 60 * 1000;
      
      if (age < maxAge) {
        return data;
      } else {
        console.log('Cache expired:', key);
        localStorage.removeItem(`cached_${key}`);
      }
    }
  } catch (error) {
    console.error('Failed to get cached data:', error);
  }
  
  return null;
}

export function clearCache() {
  const keys = Object.keys(localStorage);
  keys.forEach(key => {
    if (key.startsWith('cached_')) {
      localStorage.removeItem(key);
    }
  });
  console.log('Cache cleared');
}

export default {
  initOffline,
  queueOfflineAction,
  getOfflineQueueStatus,
  clearOfflineQueue,
  cacheEssentialData,
  getCachedData,
  clearCache
};
