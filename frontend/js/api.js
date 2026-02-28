// API client for BharatSahayak backend
const API_BASE_URL = window.location.origin;

class APIClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('auth_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      
      // Check if response is from cache
      const fromCache = response.headers.get('X-From-Cache') === 'true';
      if (fromCache) {
        console.log('Response from cache:', endpoint);
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(error.message || error.error || 'Request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Voice endpoints
  async voiceToText(audioBlob, language = null) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    if (language) {
      formData.append('language', language);
    }

    const response = await fetch(`${this.baseURL}/api/voice-to-text`, {
      method: 'POST',
      headers: {
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Voice transcription failed');
    }

    return await response.json();
  }

  async textToVoice(text, language = 'hi') {
    const response = await fetch(`${this.baseURL}/api/text-to-voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      body: JSON.stringify({ text, language })
    });

    if (!response.ok) {
      throw new Error('Voice synthesis failed');
    }

    return await response.blob();
  }

  async getSupportedLanguages() {
    return this.get('/api/languages');
  }

  // Chat/RAG endpoints
  async sendMessage(message, sessionId = null, language = 'hi') {
    return this.post('/api/ask', {
      query: message,
      session_id: sessionId,
      language
    });
  }

  async createSession(language = 'hi') {
    return this.post('/api/session/create', { language });
  }

  async deleteSession(sessionId) {
    return this.delete(`/api/session/${sessionId}`);
  }

  // Schemes endpoints
  async getSchemes(filters = {}) {
    return this.get('/api/schemes', filters);
  }

  async searchSchemes(query) {
    return this.get('/api/schemes', { search: query });
  }

  async getScheme(schemeId) {
    return this.get(`/api/schemes/${schemeId}`);
  }

  async checkEligibility(schemeId, userProfile) {
    return this.post('/api/schemes/check-eligibility', {
      scheme_id: schemeId,
      user_profile: userProfile
    });
  }

  async getEligibleSchemes(userProfile) {
    return this.post('/api/schemes/eligible', { user_profile: userProfile });
  }

  // Farmer endpoints
  async getCropAdvice(farmProfile, season) {
    return this.post('/api/farmer/crop-advice', {
      farm_profile: farmProfile,
      season
    });
  }

  async getFertilizerAdvice(crop, soilData, growthStage) {
    return this.post('/api/farmer/fertilizer-advice', {
      crop,
      soil_data: soilData,
      growth_stage: growthStage
    });
  }

  async getMandiPrices(crop = null, location = null) {
    const params = {};
    if (crop) params.crop = crop;
    if (location) params.location = location;
    return this.get('/api/farmer/market-price', params);
  }

  async getCropCalendar(crop, location) {
    return this.get('/api/farmer/crop-calendar', { crop, location });
  }

  // Skills endpoints
  async getSkillPrograms(filters = {}) {
    return this.get('/api/skills', filters);
  }

  async matchSkillPrograms(userProfile, preferences) {
    return this.post('/api/skills/match', {
      user_profile: userProfile,
      preferences
    });
  }

  async getJobs(filters = {}) {
    return this.get('/api/jobs', filters);
  }

  async getJobAlerts(userProfile) {
    return this.post('/api/jobs/alerts', { user_profile: userProfile });
  }

  // Health endpoints
  async checkSymptoms(symptoms, userInfo) {
    return this.post('/api/health/check', {
      symptoms,
      user_info: userInfo
    });
  }

  async getHealthFacilities(location = null, facilityType = null, radius = 25) {
    const params = { radius };
    if (location) params.location = location;
    if (facilityType) params.facility_type = facilityType;
    return this.get('/api/health/facilities', params);
  }

  async getHealthSchemes() {
    return this.get('/api/health/schemes');
  }

  // Auth endpoints
  async register(phoneNumber, language = 'hi') {
    return this.post('/api/auth/register', {
      phone_number: phoneNumber,
      language
    });
  }

  async verifyOTP(phoneNumber, otp) {
    const response = await this.post('/api/auth/verify', {
      phone_number: phoneNumber,
      otp
    });
    
    if (response.token) {
      this.token = response.token;
      localStorage.setItem('auth_token', response.token);
    }
    
    return response;
  }

  async getUserProfile() {
    return this.get('/api/user/profile');
  }

  async updateUserProfile(profileData) {
    return this.put('/api/user/profile', profileData);
  }

  async deleteUserData() {
    return this.delete('/api/user/data');
  }

  // Cache endpoints
  async syncCache() {
    return this.post('/api/cache/sync');
  }

  async getCachedContent(contentType) {
    return this.get('/api/cache/content', { content_type: contentType });
  }

  // Impact tracking
  async recordEvent(eventType, eventData) {
    return this.post('/api/impact/event', {
      event_type: eventType,
      event_data: eventData
    });
  }

  // Translation endpoints
  async translate(text, sourceLang, targetLang) {
    return this.post('/api/translate', {
      text,
      source_lang: sourceLang,
      target_lang: targetLang
    });
  }

  async detectLanguage(text) {
    return this.post('/api/detect-language', { text });
  }
}

export const API = new APIClient();
export default API;
