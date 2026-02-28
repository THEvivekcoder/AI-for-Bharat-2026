// Main application entry point
import { initVoice } from './voice.js';
import { initChat } from './chat.js';
import { initOffline } from './offline.js';
import { API } from './api.js';

class BharatSahayakApp {
  constructor() {
    this.currentView = 'chat';
    this.currentLanguage = localStorage.getItem('language') || 'hi';
    this.isOnline = navigator.onLine;
    
    this.init();
  }

  async init() {
    console.log('Initializing BharatSahayak PWA...');
    
    // Register service worker
    await this.registerServiceWorker();
    
    // Initialize modules
    initVoice(this);
    initChat(this);
    initOffline(this);
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Setup network monitoring
    this.setupNetworkMonitoring();
    
    // Load initial view
    this.switchView('chat');
    
    console.log('App initialized successfully');
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration.scope);
        
        // Handle updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available
              this.showUpdateNotification();
            }
          });
        });
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  setupEventListeners() {
    // Navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const view = tab.dataset.view;
        this.switchView(view);
      });
    });

    // Language selector
    const languageBtn = document.getElementById('languageBtn');
    const languageModal = document.getElementById('languageModal');
    const closeLanguageModal = document.getElementById('closeLanguageModal');
    
    languageBtn.addEventListener('click', () => {
      languageModal.classList.remove('hidden');
    });
    
    closeLanguageModal.addEventListener('click', () => {
      languageModal.classList.add('hidden');
    });
    
    languageModal.addEventListener('click', (e) => {
      if (e.target === languageModal) {
        languageModal.classList.add('hidden');
      }
    });

    // Language options
    document.querySelectorAll('.language-option').forEach(option => {
      option.addEventListener('click', () => {
        const lang = option.dataset.lang;
        this.changeLanguage(lang);
        languageModal.classList.add('hidden');
      });
    });

    // Schemes view
    this.setupSchemesView();
    
    // Farmer view
    this.setupFarmerView();
    
    // Skills view
    this.setupSkillsView();
    
    // Health view
    this.setupHealthView();
  }

  setupNetworkMonitoring() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.updateOnlineStatus();
      this.syncOfflineData();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.updateOnlineStatus();
    });

    this.updateOnlineStatus();
  }

  updateOnlineStatus() {
    const indicator = document.getElementById('offlineIndicator');
    if (this.isOnline) {
      indicator.classList.add('hidden');
    } else {
      indicator.classList.remove('hidden');
    }
  }

  async syncOfflineData() {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-data');
        console.log('Background sync registered');
      } catch (error) {
        console.error('Background sync registration failed:', error);
      }
    }
  }

  switchView(viewName) {
    // Update navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
      view.classList.remove('active');
    });
    
    const targetView = document.getElementById(`${viewName}View`);
    if (targetView) {
      targetView.classList.add('active');
      this.currentView = viewName;
      
      // Load view data
      this.loadViewData(viewName);
    }
  }

  async loadViewData(viewName) {
    switch (viewName) {
      case 'schemes':
        await this.loadSchemes();
        break;
      case 'farmer':
        // Farmer data loaded on section click
        break;
      case 'skills':
        await this.loadSkillPrograms();
        break;
      case 'health':
        // Health data loaded on section click
        break;
    }
  }

  setupSchemesView() {
    const searchInput = document.getElementById('schemeSearch');
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        this.searchSchemes(e.target.value);
      }, 300);
    });
  }

  async loadSchemes() {
    try {
      this.showLoading('Loading schemes...');
      const schemes = await API.getSchemes();
      this.displaySchemes(schemes);
    } catch (error) {
      console.error('Failed to load schemes:', error);
      this.showError('Failed to load schemes. Please try again.');
    } finally {
      this.hideLoading();
    }
  }

  async searchSchemes(query) {
    if (!query.trim()) {
      await this.loadSchemes();
      return;
    }

    try {
      this.showLoading('Searching...');
      const schemes = await API.searchSchemes(query);
      this.displaySchemes(schemes);
    } catch (error) {
      console.error('Search failed:', error);
      this.showError('Search failed. Please try again.');
    } finally {
      this.hideLoading();
    }
  }

  displaySchemes(schemes) {
    const schemesList = document.getElementById('schemesList');
    
    if (!schemes || schemes.length === 0) {
      schemesList.innerHTML = '<p class="text-center">No schemes found.</p>';
      return;
    }

    schemesList.innerHTML = schemes.map(scheme => `
      <div class="scheme-card" data-scheme-id="${scheme.scheme_id}">
        <h3>${scheme.name}</h3>
        <p>${scheme.description}</p>
        <span class="scheme-category">${scheme.category}</span>
      </div>
    `).join('');

    // Add click handlers
    schemesList.querySelectorAll('.scheme-card').forEach(card => {
      card.addEventListener('click', () => {
        const schemeId = card.dataset.schemeId;
        this.showSchemeDetails(schemeId);
      });
    });
  }

  async showSchemeDetails(schemeId) {
    try {
      this.showLoading('Loading details...');
      const scheme = await API.getScheme(schemeId);
      // Display scheme details in modal or expanded view
      alert(`Scheme: ${scheme.name}\n\n${scheme.description}`);
    } catch (error) {
      console.error('Failed to load scheme details:', error);
      this.showError('Failed to load details.');
    } finally {
      this.hideLoading();
    }
  }

  setupFarmerView() {
    document.querySelectorAll('#farmerView .section-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#farmerView .section-btn').forEach(b => {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        
        const section = btn.dataset.section;
        this.loadFarmerSection(section);
      });
    });
  }

  async loadFarmerSection(section) {
    const content = document.getElementById('farmerContent');
    
    try {
      this.showLoading('Loading...');
      
      switch (section) {
        case 'crops':
          content.innerHTML = '<p>Crop recommendations will be displayed here based on your farm profile.</p>';
          break;
        case 'fertilizer':
          content.innerHTML = '<p>Fertilizer guidance will be displayed here.</p>';
          break;
        case 'prices':
          const prices = await API.getMandiPrices();
          this.displayMandiPrices(prices);
          break;
      }
    } catch (error) {
      console.error('Failed to load farmer section:', error);
      content.innerHTML = '<p>Failed to load data. Please try again.</p>';
    } finally {
      this.hideLoading();
    }
  }

  displayMandiPrices(prices) {
    const content = document.getElementById('farmerContent');
    
    if (!prices || prices.length === 0) {
      content.innerHTML = '<p>No price data available.</p>';
      return;
    }

    content.innerHTML = `
      <div class="prices-list">
        ${prices.map(price => `
          <div class="price-card">
            <h4>${price.crop_name}</h4>
            <p>Mandi: ${price.mandi_name}</p>
            <p>Price: ₹${price.price_per_quintal}/quintal</p>
            <p class="text-secondary">Date: ${price.price_date}</p>
          </div>
        `).join('')}
      </div>
    `;
  }

  setupSkillsView() {
    document.querySelectorAll('.skills-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.skills-tab').forEach(t => {
          t.classList.remove('active');
        });
        tab.classList.add('active');
        
        const tabType = tab.dataset.tab;
        this.loadSkillsTab(tabType);
      });
    });
  }

  async loadSkillPrograms() {
    await this.loadSkillsTab('programs');
  }

  async loadSkillsTab(tabType) {
    const content = document.getElementById('skillsContent');
    
    try {
      this.showLoading('Loading...');
      
      if (tabType === 'programs') {
        const programs = await API.getSkillPrograms();
        this.displaySkillPrograms(programs);
      } else {
        const jobs = await API.getJobs();
        this.displayJobs(jobs);
      }
    } catch (error) {
      console.error('Failed to load skills data:', error);
      content.innerHTML = '<p>Failed to load data. Please try again.</p>';
    } finally {
      this.hideLoading();
    }
  }

  displaySkillPrograms(programs) {
    const content = document.getElementById('skillsContent');
    
    if (!programs || programs.length === 0) {
      content.innerHTML = '<p>No programs available.</p>';
      return;
    }

    content.innerHTML = programs.map(program => `
      <div class="scheme-card">
        <h3>${program.name}</h3>
        <p>${program.description}</p>
        <p><strong>Duration:</strong> ${program.duration_weeks} weeks</p>
        <p><strong>Provider:</strong> ${program.provider}</p>
      </div>
    `).join('');
  }

  displayJobs(jobs) {
    const content = document.getElementById('skillsContent');
    
    if (!jobs || jobs.length === 0) {
      content.innerHTML = '<p>No jobs available.</p>';
      return;
    }

    content.innerHTML = jobs.map(job => `
      <div class="scheme-card">
        <h3>${job.title}</h3>
        <p>${job.description}</p>
        <p><strong>Department:</strong> ${job.department}</p>
        <p><strong>Deadline:</strong> ${job.application_deadline}</p>
      </div>
    `).join('');
  }

  setupHealthView() {
    document.querySelectorAll('#healthView .section-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#healthView .section-btn').forEach(b => {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        
        const section = btn.dataset.section;
        this.loadHealthSection(section);
      });
    });
  }

  async loadHealthSection(section) {
    const content = document.getElementById('healthContent');
    
    try {
      this.showLoading('Loading...');
      
      switch (section) {
        case 'symptoms':
          content.innerHTML = '<p>Symptom checker will be displayed here.</p>';
          break;
        case 'facilities':
          const facilities = await API.getHealthFacilities();
          this.displayHealthFacilities(facilities);
          break;
        case 'schemes':
          content.innerHTML = '<p>Health schemes will be displayed here.</p>';
          break;
      }
    } catch (error) {
      console.error('Failed to load health section:', error);
      content.innerHTML = '<p>Failed to load data. Please try again.</p>';
    } finally {
      this.hideLoading();
    }
  }

  displayHealthFacilities(facilities) {
    const content = document.getElementById('healthContent');
    
    if (!facilities || facilities.length === 0) {
      content.innerHTML = '<p>No facilities found nearby.</p>';
      return;
    }

    content.innerHTML = facilities.map(facility => `
      <div class="scheme-card">
        <h3>${facility.name}</h3>
        <p><strong>Type:</strong> ${facility.facility_type}</p>
        <p><strong>Location:</strong> ${facility.district}, ${facility.state}</p>
        <p><strong>Contact:</strong> ${facility.contact || 'N/A'}</p>
      </div>
    `).join('');
  }

  changeLanguage(lang) {
    this.currentLanguage = lang;
    localStorage.setItem('language', lang);
    console.log('Language changed to:', lang);
    // Reload current view with new language
    this.loadViewData(this.currentView);
  }

  showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const text = document.getElementById('loadingText');
    text.textContent = message;
    overlay.classList.remove('hidden');
  }

  hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('hidden');
  }

  showError(message) {
    alert(message); // Replace with better error UI
  }

  showUpdateNotification() {
    if (confirm('A new version is available. Reload to update?')) {
      window.location.reload();
    }
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.app = new BharatSahayakApp();
  });
} else {
  window.app = new BharatSahayakApp();
}

export default BharatSahayakApp;
