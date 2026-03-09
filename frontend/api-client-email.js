/**
 * BharatSahayak API Client - Email/Password Authentication
 * Updated to support email/password login with JWT tokens
 */

class BharatSahayakAPI {
    constructor() {
        this.config = null;
        this.authToken = null;
        this.currentUser = null;
        this.retryAttempts = 3;
        this.retryDelay = 1000;
        this.timeout = 30000;
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) return;

        try {
            await this.loadConfig();
            this.loadAuthState();
            this.initialized = true;
            console.log('✅ BharatSahayak API Client initialized');
            console.log('📍 API Endpoint:', this.config.apiEndpoint);
            console.log('🔐 Authenticated:', !!this.authToken);
        } catch (error) {
            console.error('❌ Failed to initialize API client:', error);
            throw error;
        }
    }

    async loadConfig() {
        this.config = {
            apiEndpoint: 'https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev',
            environment: 'development',
            retryAttempts: 3,
            retryDelay: 1000,
            timeout: 30000
        };

        try {
            const savedConfig = localStorage.getItem('bharatsahayak-config');
            if (savedConfig) {
                this.config = { ...this.config, ...JSON.parse(savedConfig) };
            }

            const response = await fetch('/config.json', { 
                cache: 'no-cache',
                headers: { 'Cache-Control': 'no-cache' }
            });
            
            if (response.ok) {
                const serverConfig = await response.json();
                this.config = { ...this.config, ...serverConfig };
                localStorage.setItem('bharatsahayak-config', JSON.stringify(this.config));
            }
        } catch (error) {
            console.warn('⚠️ Could not load server config, using defaults');
        }

        if (this.config.apiEndpoint.endsWith('/')) {
            this.config.apiEndpoint = this.config.apiEndpoint.slice(0, -1);
        }

        this.retryAttempts = this.config.retryAttempts || 3;
        this.retryDelay = this.config.retryDelay || 1000;
        this.timeout = this.config.timeout || 30000;
    }

    loadAuthState() {
        this.authToken = localStorage.getItem('bharatsahayak-auth-token');
        const userStr = localStorage.getItem('bharatsahayak-user');
        
        if (userStr) {
            try {
                this.currentUser = JSON.parse(userStr);
            } catch (e) {
                console.error('Failed to parse user data:', e);
                this.currentUser = null;
            }
        }
    }

    saveAuthState(token, user) {
        this.authToken = token;
        this.currentUser = user;
        localStorage.setItem('bharatsahayak-auth-token', token);
        localStorage.setItem('bharatsahayak-user', JSON.stringify(user));
    }

    clearAuthState() {
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('bharatsahayak-auth-token');
        localStorage.removeItem('bharatsahayak-user');
        localStorage.removeItem('bharatsahayak-guest');
    }

    isAuthenticated() {
        return !!this.authToken && !!this.currentUser;
    }

    isGuest() {
        return localStorage.getItem('bharatsahayak-guest') === 'true';
    }

    async request(endpoint, options = {}) {
        if (!this.initialized) {
            await this.initialize();
        }

        const url = `${this.config.apiEndpoint}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.authToken && !options.skipAuth) {
            defaultHeaders['Authorization'] = `Bearer ${this.authToken}`;
        }

        const requestOptions = {
            ...options,
            headers: defaultHeaders
        };

        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                console.log(`🌐 API Request [${attempt}/${this.retryAttempts}]: ${options.method || 'GET'} ${endpoint}`);

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(url, {
                    ...requestOptions,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                let data;
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }

                if (response.ok) {
                    console.log(`✅ API Success: ${endpoint}`);
                    return { success: true, data, status: response.status };
                } else {
                    if (response.status === 401) {
                        console.warn('🔒 Authentication required');
                        this.clearAuthState();
                        if (window.location.pathname !== '/login.html' && !window.location.pathname.includes('landing')) {
                            window.location.href = 'login.html';
                        }
                        return { success: false, error: 'Authentication required', status: 401 };
                    }

                    const errorMessage = data.error || data.message || `Request failed with status ${response.status}`;
                    console.error(`❌ API Error: ${endpoint} - ${errorMessage}`);
                    
                    return { 
                        success: false, 
                        error: errorMessage, 
                        status: response.status,
                        data
                    };
                }
            } catch (error) {
                console.error(`❌ API Request failed [${attempt}/${this.retryAttempts}]:`, error.message);
                
                if (attempt === this.retryAttempts) {
                    if (error.name === 'AbortError') {
                        return { success: false, error: 'Request timeout', status: 408 };
                    }
                    return { success: false, error: 'Network error. Please check your connection.', status: 0 };
                }
                
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
            }
        }
    }

    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    // ==================== Email/Password Authentication ====================

    async registerWithEmail(email, password, name) {
        const result = await this.post('/auth/email/register', {
            email,
            password,
            name
        }, { skipAuth: true });
        return result;
    }

    async loginWithEmail(email, password) {
        const result = await this.post('/auth/email/login', {
            email,
            password
        }, { skipAuth: true });
        
        if (result.success && result.data.access_token) {
            this.saveAuthState(result.data.access_token, {
                user_id: result.data.user_id,
                email: result.data.email,
                name: result.data.name,
                profile_completed: result.data.profile_completed
            });
        }
        
        return result;
    }

    async logout() {
        this.clearAuthState();
        window.location.href = 'login.html';
    }

    // ==================== Dashboard APIs ====================

    async getDashboardData() {
        return this.get('/dashboard/data');
    }

    // ==================== User Profile APIs ====================

    async getUserProfile() {
        return this.get('/user/profile');
    }

    async updateUserProfile(profileData) {
        return this.put('/user/profile', profileData);
    }

    async getUserStats() {
        return this.get('/user/stats');
    }

    // ==================== Schemes APIs ====================

    async getAllSchemes(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/schemes?${queryString}` : '/schemes';
        return this.get(endpoint);
    }

    async searchSchemes(query, filters = {}) {
        const params = { query, ...filters };
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/schemes/search?${queryString}`);
    }

    async getSchemeDetails(schemeId) {
        return this.get(`/schemes/${schemeId}`);
    }

    async getEligibleSchemes() {
        return this.get('/schemes/eligible');
    }

    async checkEligibility(schemeId) {
        return this.post('/schemes/check-eligibility', { scheme_id: schemeId });
    }

    async saveScheme(schemeId, schemeName) {
        return this.post('/schemes/save', {
            scheme_id: schemeId,
            scheme_name: schemeName,
            action: 'save'
        });
    }

    async unsaveScheme(schemeId) {
        return this.post('/schemes/save', {
            scheme_id: schemeId,
            action: 'unsave'
        });
    }

    // ==================== Agriculture APIs ====================

    async getCropAdvice(location, season) {
        const params = { location, season };
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/crop-advice?${queryString}`);
    }

    async getMarketPrices(location, commodity) {
        const params = { location, commodity };
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/market-prices?${queryString}`);
    }

    // ==================== Voice APIs ====================

    async voiceToText(audioData, language) {
        return this.post('/voice-to-text', {
            audio_data: audioData,
            language: language
        });
    }

    async conversationalQuery(query, language) {
        return this.post('/conversational-query', {
            query: query,
            language: language
        });
    }

    // ==================== Analytics APIs ====================

    async trackEvent(eventType, eventData) {
        return this.post('/analytics/track', {
            event_type: eventType,
            event_data: eventData
        });
    }

    async getAnalytics() {
        return this.get('/analytics/dashboard');
    }
}

// Create global instance
const api = new BharatSahayakAPI();

// Initialize on page load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            await api.initialize();
            console.log('🚀 API Client ready');
            window.dispatchEvent(new CustomEvent('api-ready'));
        } catch (error) {
            console.error('Failed to initialize API:', error);
        }
    });
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.api = api;
    window.BharatSahayakAPI = BharatSahayakAPI;
}
