// API Client for BharatSahayak AWS Backend

// Load config
const API_CONFIG = window.CONFIG ? window.CONFIG.api : {
  baseURL: 'https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev'
};

// Demo mode flag - set to true to bypass API calls for testing
const DEMO_MODE = true;

class APIClient {
  constructor() {
    this.baseURL = API_CONFIG.baseURL;
    this.demoMode = DEMO_MODE;
  }

  // Get auth token from storage
  getAuthToken() {
    return storage.get('authToken');
  }

  // Set auth token
  setAuthToken(token) {
    storage.set('authToken', token);
  }

  // Make API request
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    if (token && !options.skipAuth) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    console.log('API Request:', { url, method: options.method || 'GET', headers });
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
        mode: 'cors' // Explicitly set CORS mode
      });
      
      console.log('API Response:', { status: response.status, statusText: response.statusText });
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error('Non-JSON response:', text);
        throw new Error('Invalid response format from server');
      }
      
      if (!response.ok) {
        throw new Error(data.message || data.error || `API Error: ${response.status}`);
      }
      
      return data;
    } catch (error) {
      console.error('API Error Details:', {
        endpoint,
        error: error.message,
        stack: error.stack
      });
      
      // Provide user-friendly error messages
      if (error.message === 'Failed to fetch') {
        throw new Error('Cannot connect to server. Please check your internet connection or try again later.');
      }
      
      throw error;
    }
  }

  // Auth APIs
  async register(userData) {
    if (this.demoMode) {
      // Demo mode - simulate successful registration
      return {
        success: true,
        message: 'Registration successful (Demo Mode)',
        user_id: 'demo_user_' + Date.now()
      };
    }
    
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        phone_number: userData.phone,
        email: userData.email,
        name: userData.name,
        password: userData.password
      }),
      skipAuth: true
    });
  }

  async verifyOTP(phone, otp) {
    if (this.demoMode) {
      // Demo mode - simulate successful OTP verification
      return {
        success: true,
        token: 'demo_token_' + Date.now(),
        user_id: 'demo_user_' + Date.now()
      };
    }
    
    return this.request('/auth/verify', {
      method: 'POST',
      body: JSON.stringify({
        phone_number: phone,
        otp: otp
      }),
      skipAuth: true
    });
  }

  async login(phoneOrEmail, password) {
    if (this.demoMode) {
      // Demo mode - simulate successful login
      return {
        success: true,
        token: 'demo_token_' + Date.now(),
        user_id: 'demo_user_' + Date.now(),
        name: phoneOrEmail.split('@')[0],
        email: phoneOrEmail,
        phone_number: phoneOrEmail
      };
    }
    
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        phone_number: phoneOrEmail,
        password: password
      }),
      skipAuth: true
    });
  }

  // User Profile APIs
  async getProfile() {
    if (this.demoMode) {
      return { profile: storage.get('userProfile') || {} };
    }
    
    return this.request('/user/profile', {
      method: 'GET'
    });
  }

  async updateProfile(profileData) {
    if (this.demoMode) {
      storage.set('userProfile', profileData);
      return { success: true, profile: profileData };
    }
    
    return this.request('/user/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async getUserStats() {
    if (this.demoMode) {
      return {
        total_interactions: 0,
        saved_schemes: savedSchemes.getAll().length
      };
    }
    
    return this.request('/user/stats', {
      method: 'GET'
    });
  }

  // Schemes APIs
  async searchSchemes(query = '', category = '') {
    if (this.demoMode) {
      // Use local search in demo mode
      return { schemes: searchSchemesLocal(query, { category }) };
    }
    
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category && category !== 'all') params.append('category', category);
    
    return this.request(`/schemes?${params.toString()}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  async getSchemeDetails(schemeId) {
    if (this.demoMode) {
      // Use local data in demo mode
      const scheme = schemesData.find(s => s.id === schemeId || s.slug === schemeId);
      return { scheme: scheme };
    }
    
    return this.request(`/schemes/${schemeId}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  async checkEligibility(schemeId, userProfile) {
    return this.request('/schemes/check-eligibility', {
      method: 'POST',
      body: JSON.stringify({
        scheme_id: schemeId,
        user_profile: userProfile
      })
    });
  }

  async getEligibleSchemes() {
    return this.request('/schemes/eligible', {
      method: 'GET'
    });
  }

  // Voice APIs
  async voiceToText(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    
    return this.request('/voice-to-text', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    });
  }

  async textToVoice(text, language = 'en') {
    return this.request('/voice/synthesize', {
      method: 'POST',
      body: JSON.stringify({
        text: text,
        language: language
      }),
      skipAuth: true
    });
  }

  async detectLanguage(text) {
    return this.request('/voice/detect-language', {
      method: 'POST',
      body: JSON.stringify({
        text: text
      }),
      skipAuth: true
    });
  }

  // Conversational Query
  async conversationalQuery(query, context = {}) {
    return this.request('/conversational-query', {
      method: 'POST',
      body: JSON.stringify({
        query: query,
        context: context
      }),
      skipAuth: true
    });
  }

  // Translation
  async translateScheme(schemeId, targetLanguage) {
    return this.request('/translate/scheme', {
      method: 'POST',
      body: JSON.stringify({
        scheme_id: schemeId,
        target_language: targetLanguage
      }),
      skipAuth: true
    });
  }

  // Agriculture APIs
  async getCropAdvice(location, soilType) {
    const params = new URLSearchParams();
    if (location) params.append('location', location);
    if (soilType) params.append('soil_type', soilType);
    
    return this.request(`/crop-advice?${params.toString()}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  async getMarketPrices(crop, location) {
    const params = new URLSearchParams();
    if (crop) params.append('crop', crop);
    if (location) params.append('location', location);
    
    return this.request(`/market-prices?${params.toString()}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  // Skills & Jobs APIs
  async matchSkills(skills) {
    return this.request('/skills/match', {
      method: 'POST',
      body: JSON.stringify({
        skills: skills
      })
    });
  }

  async searchJobs(query = '', location = '') {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (location) params.append('location', location);
    
    return this.request(`/jobs?${params.toString()}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  // Health APIs
  async getHealthFacilities(location, type = '') {
    const params = new URLSearchParams();
    if (location) params.append('location', location);
    if (type) params.append('type', type);
    
    return this.request(`/health/facilities?${params.toString()}`, {
      method: 'GET',
      skipAuth: true
    });
  }

  async healthCheck() {
    return this.request('/health-check', {
      method: 'GET',
      skipAuth: true
    });
  }
}

// Create global API client instance
const api = new APIClient();
