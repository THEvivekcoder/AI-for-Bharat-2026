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
    storage.remove('savedSchemes');
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

// Sample Schemes Data
const sampleSchemes = [
  {
    id: 'pmkvy-2024',
    title: 'Pradhan Mantri Kaushal Vikas Yojana',
    category: 'skill_development',
    description: 'Skill development scheme providing free training and certification',
    eligibility: 'Age 18-35, Indian citizen',
    benefits: 'Free training, certification, job placement assistance',
    documents: ['Aadhaar Card', 'Age Proof', 'Address Proof'],
    steps: ['Visit nearest training center', 'Register with Aadhaar', 'Choose training program', 'Complete training'],
    link: 'https://www.pmkvyofficial.org'
  },
  {
    id: 'pmay-2024',
    title: 'Pradhan Mantri Awas Yojana',
    category: 'housing',
    description: 'Housing for all scheme providing financial assistance for home construction',
    eligibility: 'EWS/LIG/MIG families, no pucca house',
    benefits: 'Subsidy up to ₹2.67 lakh, low interest rates',
    documents: ['Income Certificate', 'Aadhaar Card', 'Property Documents'],
    steps: ['Apply online', 'Submit documents', 'Verification', 'Subsidy approval'],
    link: 'https://pmaymis.gov.in'
  },
  {
    id: 'pmfby-2024',
    title: 'Pradhan Mantri Fasal Bima Yojana',
    category: 'agriculture',
    description: 'Crop insurance scheme protecting farmers against crop loss',
    eligibility: 'All farmers growing notified crops',
    benefits: 'Comprehensive risk coverage, low premium',
    documents: ['Land Records', 'Aadhaar Card', 'Bank Account'],
    steps: ['Contact bank/CSC', 'Fill application', 'Pay premium', 'Get policy'],
    link: 'https://pmfby.gov.in'
  }
];

// Search Functionality
function searchSchemes(query, filters = {}) {
  let results = [...sampleSchemes];
  
  if (query) {
    const lowerQuery = query.toLowerCase();
    results = results.filter(scheme => 
      scheme.title.toLowerCase().includes(lowerQuery) ||
      scheme.description.toLowerCase().includes(lowerQuery) ||
      scheme.category.toLowerCase().includes(lowerQuery)
    );
  }
  
  if (filters.category && filters.category !== 'all') {
    results = results.filter(scheme => scheme.category === filters.category);
  }
  
  return results;
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
  
  container.innerHTML = schemes.map(scheme => `
    <div class="scheme-card" onclick="viewScheme('${scheme.id}')">
      <span class="scheme-badge badge-${scheme.category}">${formatCategory(scheme.category)}</span>
      <h3 class="mb-2">${scheme.title}</h3>
      <p class="text-muted mb-2">${scheme.description}</p>
      <div class="flex-between">
        <span class="text-muted" style="font-size: 0.875rem;">📋 ${scheme.eligibility}</span>
        <button class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.875rem;">View Details</button>
      </div>
    </div>
  `).join('');
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

// Get Scheme by ID
function getSchemeById(id) {
  return sampleSchemes.find(scheme => scheme.id === id);
}

// Toggle Save Scheme
function toggleSaveScheme(schemeId) {
  const scheme = getSchemeById(schemeId);
  if (!scheme) return;
  
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
