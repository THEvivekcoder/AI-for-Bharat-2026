// Modern UI - Main JavaScript

// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.nav-links');
  
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  // Sidebar Toggle for Dashboard
  const menuToggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('active');
    });
  }

  // Active Navigation Link
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const navItems = document.querySelectorAll('.sidebar-nav a');
  
  navItems.forEach(item => {
    if (item.getAttribute('href') === currentPage) {
      item.classList.add('active');
    }
  });
});

// Local Storage Helpers
const storage = {
  get: (key) => {
    try {
      return JSON.parse(localStorage.getItem(key));
    } catch {
      return null;
    }
  },
  set: (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
  },
  remove: (key) => {
    localStorage.removeItem(key);
  }
};

// Auth Helpers
const auth = {
  isLoggedIn: () => !!storage.get('user'),
  getUser: () => storage.get('user'),
  setUser: (user) => storage.set('user', user),
  logout: () => {
    storage.remove('user');
    storage.remove('authToken');
    storage.remove('savedSchemes');
    storage.remove('profileComplete');
    storage.remove('userProfile');
    storage.remove('pendingUser');
    window.location.href = 'index.html';
  },
  loginAsGuest: () => {
    const guestUser = {
      id: 'guest_' + Date.now(),
      name: 'Guest User',
      email: 'guest@example.com',
      isGuest: true
    };
    auth.setUser(guestUser);
    storage.set('profileComplete', true);
    window.location.href = 'dashboard.html';
  }
};

// Saved Schemes Helpers
const savedSchemes = {
  getAll: () => storage.get('savedSchemes') || [],
  add: (scheme) => {
    const schemes = savedSchemes.getAll();
    if (!schemes.find(s => s.id === scheme.id)) {
      schemes.push(scheme);
      storage.set('savedSchemes', schemes);
      return true;
    }
    return false;
  },
  remove: (schemeId) => {
    const schemes = savedSchemes.getAll().filter(s => s.id !== schemeId);
    storage.set('savedSchemes', schemes);
  },
  isSaved: (schemeId) => {
    return savedSchemes.getAll().some(s => s.id === schemeId);
  }
};

// Search Functionality (local filtering)
function searchSchemesLocal(query, filters = {}) {
  if (!window.schemesData || window.schemesData.length === 0) {
    return [];
  }
  
  let results = [...window.schemesData];
  
  if (query) {
    const lowerQuery = query.toLowerCase();
    results = results.filter(scheme => 
      (scheme.name && scheme.name.toLowerCase().includes(lowerQuery)) ||
      (scheme.details && scheme.details.toLowerCase().includes(lowerQuery)) ||
      (scheme.category && scheme.category.toLowerCase().includes(lowerQuery)) ||
      (scheme.tags && scheme.tags.toLowerCase().includes(lowerQuery))
    );
  }
  
  if (filters.category && filters.category !== 'all') {
    results = results.filter(scheme => 
      scheme.category && scheme.category.toLowerCase().includes(filters.category.toLowerCase())
    );
  }
  
  if (filters.level && filters.level !== 'all') {
    results = results.filter(scheme => 
      scheme.level && scheme.level.toLowerCase() === filters.level.toLowerCase()
    );
  }
  
  return results;
}

// Search via API (with fallback to local)
async function searchSchemes(query, filters = {}) {
  try {
    const response = await api.searchSchemes(query, filters.category);
    return response.schemes || [];
  } catch (error) {
    return searchSchemesLocal(query, filters);
  }
}

// Render Scheme Cards
function renderSchemeCards(schemes, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  if (schemes.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h3>No schemes found</h3>
        <p>Try adjusting your search or filters</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = schemes.slice(0, 50).map(scheme => `
    <div class="scheme-card" onclick="viewScheme('${scheme.id}')">
      <span class="scheme-badge badge-${getCategoryClass(scheme.category)}">${scheme.category || 'General'}</span>
      <h3 class="mb-2">${scheme.name || 'Untitled Scheme'}</h3>
      <p class="text-muted mb-2">${truncateText(scheme.details || scheme.benefits || 'No description available', 120)}</p>
      <div class="flex-between">
        <span class="text-muted" style="font-size: 0.875rem;">📋 ${scheme.level || 'N/A'}</span>
        <button class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.875rem;">View Details</button>
      </div>
    </div>
  `).join('');
}

function getCategoryClass(category) {
  if (!category) return 'skill';
  const cat = category.toLowerCase();
  if (cat.includes('education')) return 'education';
  if (cat.includes('health')) return 'health';
  if (cat.includes('agriculture') || cat.includes('rural')) return 'agriculture';
  return 'skill';
}

function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Format Category
function formatCategory(category) {
  return category.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
}

// View Scheme Details
function viewScheme(schemeId) {
  window.location.href = `details.html?id=${schemeId}`;
}

// Get Scheme by ID (from API or local)
async function getSchemeById(id) {
  if (!id) return null;
  
  try {
    if (api.demoMode) {
      return window.schemesData.find(scheme => scheme.id === id || scheme.slug === id);
    }
    
    const response = await api.getSchemeDetails(id);
    return response.scheme || null;
  } catch (error) {
    return window.schemesData.find(scheme => scheme.id === id || scheme.slug === id);
  }
}

// Toggle Save Scheme
function toggleSaveScheme(schemeId) {
  const scheme = window.schemesData.find(s => s.id === schemeId || s.slug === schemeId);
  if (!scheme) {
    return false;
  }
  
  if (savedSchemes.isSaved(schemeId)) {
    savedSchemes.remove(schemeId);
    return false;
  } else {
    savedSchemes.add(scheme);
    return true;
  }
}

// Show Alert
function showAlert(message, type = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} fade-in`;
  alertDiv.textContent = message;
  
  const container = document.querySelector('.content-area') || document.body;
  container.insertBefore(alertDiv, container.firstChild);
  
  setTimeout(() => {
    alertDiv.remove();
  }, 3000);
}
