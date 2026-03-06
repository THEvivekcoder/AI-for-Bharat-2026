// Global state
let config = {
    apiEndpoint: '',
    userPoolId: '',
    clientId: ''
};

let authToken = null;
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadAuthState();
});

// Configuration Management
function saveConfig() {
    config.apiEndpoint = document.getElementById('api-endpoint').value.trim();
    config.userPoolId = document.getElementById('user-pool-id').value.trim();
    config.clientId = document.getElementById('client-id').value.trim();
    
    if (!config.apiEndpoint || !config.userPoolId || !config.clientId) {
        showStatus('config-status', 'Please fill in all configuration fields', 'error');
        return;
    }
    
    // Remove trailing slash from API endpoint
    if (config.apiEndpoint.endsWith('/')) {
        config.apiEndpoint = config.apiEndpoint.slice(0, -1);
    }
    
    localStorage.setItem('bharatsahayak-config', JSON.stringify(config));
    showStatus('config-status', 'Configuration saved successfully!', 'success');
}

function loadConfig() {
    const saved = localStorage.getItem('bharatsahayak-config');
    if (saved) {
        config = JSON.parse(saved);
        document.getElementById('api-endpoint').value = config.apiEndpoint;
        document.getElementById('user-pool-id').value = config.userPoolId;
        document.getElementById('client-id').value = config.clientId;
    }
}

// Authentication
async function register() {
    const phone = document.getElementById('reg-phone').value.trim();
    const language = document.getElementById('reg-language').value;
    
    if (!phone) {
        showStatus('reg-status', 'Please enter phone number', 'error');
        return;
    }
    
    if (!config.apiEndpoint) {
        showStatus('reg-status', 'Please configure API endpoint first', 'error');
        return;
    }
    
    try {
        showStatus('reg-status', 'Registering...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone_number: phone,
                language: language
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('reg-status', 'Registration successful! Check your phone for OTP', 'success');
            document.getElementById('login-phone').value = phone;
        } else {
            showStatus('reg-status', `Error: ${data.message || 'Registration failed'}`, 'error');
        }
    } catch (error) {
        showStatus('reg-status', `Error: ${error.message}`, 'error');
    }
}

async function verifyOTP() {
    const phone = document.getElementById('login-phone').value.trim();
    const otp = document.getElementById('login-otp').value.trim();
    
    if (!phone || !otp) {
        showStatus('login-status', 'Please enter phone number and OTP', 'error');
        return;
    }
    
    if (!config.apiEndpoint) {
        showStatus('login-status', 'Please configure API endpoint first', 'error');
        return;
    }
    
    try {
        showStatus('login-status', 'Verifying...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone_number: phone,
                otp: otp
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = phone;
            
            localStorage.setItem('bharatsahayak-token', authToken);
            localStorage.setItem('bharatsahayak-user', currentUser);
            
            showStatus('login-status', 'Login successful!', 'success');
            updateUIAfterLogin();
        } else {
            showStatus('login-status', `Error: ${data.message || 'Verification failed'}`, 'error');
        }
    } catch (error) {
        showStatus('login-status', `Error: ${error.message}`, 'error');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('bharatsahayak-token');
    localStorage.removeItem('bharatsahayak-user');
    updateUIAfterLogout();
    showStatus('login-status', 'Logged out successfully', 'info');
}

function loadAuthState() {
    authToken = localStorage.getItem('bharatsahayak-token');
    currentUser = localStorage.getItem('bharatsahayak-user');
    
    if (authToken && currentUser) {
        updateUIAfterLogin();
    }
}

function updateUIAfterLogin() {
    document.getElementById('auth-info').style.display = 'block';
    document.getElementById('current-user').textContent = currentUser;
    document.getElementById('profile-section').style.display = 'block';
    document.getElementById('eligibility-section').style.display = 'block';
    document.getElementById('analytics-section').style.display = 'block';
}

function updateUIAfterLogout() {
    document.getElementById('auth-info').style.display = 'none';
    document.getElementById('profile-section').style.display = 'none';
    document.getElementById('eligibility-section').style.display = 'none';
    document.getElementById('analytics-section').style.display = 'none';
}

// User Profile Management
async function getProfile() {
    if (!authToken) {
        showStatus('profile-status', 'Please login first', 'error');
        return;
    }
    
    try {
        showStatus('profile-status', 'Loading profile...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/user/profile`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            populateProfileForm(data);
            showStatus('profile-status', 'Profile loaded successfully', 'success');
        } else {
            showStatus('profile-status', `Error: ${data.message || 'Failed to load profile'}`, 'error');
        }
    } catch (error) {
        showStatus('profile-status', `Error: ${error.message}`, 'error');
    }
}

async function updateProfile() {
    if (!authToken) {
        showStatus('profile-status', 'Please login first', 'error');
        return;
    }
    
    const profile = {
        age: parseInt(document.getElementById('profile-age').value) || null,
        gender: document.getElementById('profile-gender').value || null,
        education_level: document.getElementById('profile-education').value || null,
        occupation: document.getElementById('profile-occupation').value || null,
        income_bracket: document.getElementById('profile-income').value || null,
        location: {
            state: document.getElementById('profile-state').value || null,
            district: document.getElementById('profile-district').value || null,
            pincode: document.getElementById('profile-pincode').value || null
        }
    };
    
    try {
        showStatus('profile-status', 'Updating profile...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/user/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profile)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('profile-status', 'Profile updated successfully!', 'success');
        } else {
            showStatus('profile-status', `Error: ${data.message || 'Failed to update profile'}`, 'error');
        }
    } catch (error) {
        showStatus('profile-status', `Error: ${error.message}`, 'error');
    }
}

function populateProfileForm(profile) {
    document.getElementById('profile-age').value = profile.age || '';
    document.getElementById('profile-gender').value = profile.gender || '';
    document.getElementById('profile-education').value = profile.education_level || '';
    document.getElementById('profile-occupation').value = profile.occupation || '';
    document.getElementById('profile-income').value = profile.income_bracket || '';
    
    if (profile.location) {
        document.getElementById('profile-state').value = profile.location.state || '';
        document.getElementById('profile-district').value = profile.location.district || '';
        document.getElementById('profile-pincode').value = profile.location.pincode || '';
    }
}

// Scheme Search
async function searchSchemes() {
    const query = document.getElementById('search-query').value.trim();
    const category = document.getElementById('search-category').value;
    const state = document.getElementById('search-state').value.trim();
    
    if (!config.apiEndpoint) {
        showStatus('search-status', 'Please configure API endpoint first', 'error');
        return;
    }
    
    try {
        showStatus('search-status', 'Searching...', 'info');
        
        const params = new URLSearchParams();
        if (query) params.append('query', query);
        if (category) params.append('category', category);
        if (state) params.append('state', state);
        
        const response = await fetch(`${config.apiEndpoint}/schemes?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySchemes(data.schemes || []);
            showStatus('search-status', `Found ${data.schemes?.length || 0} schemes`, 'success');
        } else {
            showStatus('search-status', `Error: ${data.message || 'Search failed'}`, 'error');
        }
    } catch (error) {
        showStatus('search-status', `Error: ${error.message}`, 'error');
    }
}

async function browseAllSchemes() {
    document.getElementById('search-query').value = '';
    document.getElementById('search-category').value = '';
    document.getElementById('search-state').value = '';
    await searchSchemes();
}

function displaySchemes(schemes) {
    const container = document.getElementById('search-results');
    
    if (schemes.length === 0) {
        container.innerHTML = '<p style="color: #6c757d; text-align: center; padding: 20px;">No schemes found</p>';
        return;
    }
    
    container.innerHTML = schemes.map(scheme => `
        <div class="scheme-card">
            <h4>${scheme.name}</h4>
            <p><strong>Category:</strong> ${scheme.category}</p>
            <p><strong>Department:</strong> ${scheme.department || 'N/A'}</p>
            ${scheme.state ? `<p><strong>State:</strong> ${scheme.state}</p>` : ''}
            <p>${scheme.description || 'No description available'}</p>
            <div>
                <span class="badge">${scheme.category}</span>
                ${scheme.state ? `<span class="badge">${scheme.state}</span>` : '<span class="badge">Central</span>'}
            </div>
            <button onclick="viewSchemeDetails('${scheme.scheme_id}')" class="btn btn-primary btn-small">View Details</button>
            <button onclick="selectSchemeForEligibility('${scheme.scheme_id}')" class="btn btn-secondary btn-small">Check Eligibility</button>
        </div>
    `).join('');
}

async function viewSchemeDetails(schemeId) {
    try {
        const response = await fetch(`${config.apiEndpoint}/schemes/${schemeId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySchemeDetailsModal(data);
        } else {
            alert(`Error: ${data.message || 'Failed to load scheme details'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function displaySchemeDetailsModal(scheme) {
    const details = `
        <div style="background: white; padding: 20px; border-radius: 8px; max-width: 800px; margin: 20px auto;">
            <h3>${scheme.name}</h3>
            <p><strong>Category:</strong> ${scheme.category}</p>
            <p><strong>Department:</strong> ${scheme.department || 'N/A'}</p>
            ${scheme.state ? `<p><strong>State:</strong> ${scheme.state}</p>` : ''}
            <p><strong>Description:</strong> ${scheme.description || 'N/A'}</p>
            
            ${scheme.benefits && scheme.benefits.length > 0 ? `
                <h4>Benefits:</h4>
                <ul>${scheme.benefits.map(b => `<li>${b}</li>`).join('')}</ul>
            ` : ''}
            
            ${scheme.eligibility_criteria ? `
                <h4>Eligibility Criteria:</h4>
                <pre class="code-block">${JSON.stringify(scheme.eligibility_criteria, null, 2)}</pre>
            ` : ''}
            
            ${scheme.required_documents && scheme.required_documents.length > 0 ? `
                <h4>Required Documents:</h4>
                <ul>${scheme.required_documents.map(d => `<li>${d}</li>`).join('')}</ul>
            ` : ''}
            
            ${scheme.application_process && scheme.application_process.length > 0 ? `
                <h4>Application Process:</h4>
                <ol>${scheme.application_process.map(s => `<li>${s}</li>`).join('')}</ol>
            ` : ''}
            
            ${scheme.application_url ? `
                <p><strong>Application URL:</strong> <a href="${scheme.application_url}" target="_blank">${scheme.application_url}</a></p>
            ` : ''}
        </div>
    `;
    
    // Simple modal display
    const modal = window.open('', 'Scheme Details', 'width=900,height=700,scrollbars=yes');
    modal.document.write(`
        <html>
        <head>
            <title>${scheme.name}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h3 { color: #667eea; }
                h4 { color: #555; margin-top: 20px; }
                .code-block { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }
            </style>
        </head>
        <body>${details}</body>
        </html>
    `);
}

function selectSchemeForEligibility(schemeId) {
    document.getElementById('scheme-id').value = schemeId;
    document.getElementById('eligibility-section').scrollIntoView({ behavior: 'smooth' });
}

// Eligibility Checking
async function checkEligibility() {
    if (!authToken) {
        showStatus('eligibility-status', 'Please login first', 'error');
        return;
    }
    
    const schemeId = document.getElementById('scheme-id').value.trim();
    
    if (!schemeId) {
        showStatus('eligibility-status', 'Please enter a scheme ID', 'error');
        return;
    }
    
    // Get current profile data
    const userProfile = {
        age: parseInt(document.getElementById('profile-age').value) || null,
        gender: document.getElementById('profile-gender').value || null,
        education_level: document.getElementById('profile-education').value || null,
        occupation: document.getElementById('profile-occupation').value || null,
        income_bracket: document.getElementById('profile-income').value || null,
        location: {
            state: document.getElementById('profile-state').value || null,
            district: document.getElementById('profile-district').value || null,
            pincode: document.getElementById('profile-pincode').value || null
        }
    };
    
    try {
        showStatus('eligibility-status', 'Checking eligibility...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/schemes/check-eligibility`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scheme_id: schemeId,
                user_profile: userProfile
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayEligibilityResult(data);
            showStatus('eligibility-status', 'Eligibility check complete', 'success');
        } else {
            showStatus('eligibility-status', `Error: ${data.message || 'Eligibility check failed'}`, 'error');
        }
    } catch (error) {
        showStatus('eligibility-status', `Error: ${error.message}`, 'error');
    }
}

async function getAllEligibleSchemes() {
    if (!authToken) {
        showStatus('eligibility-status', 'Please login first', 'error');
        return;
    }
    
    const userProfile = {
        age: parseInt(document.getElementById('profile-age').value) || null,
        gender: document.getElementById('profile-gender').value || null,
        education_level: document.getElementById('profile-education').value || null,
        occupation: document.getElementById('profile-occupation').value || null,
        income_bracket: document.getElementById('profile-income').value || null,
        location: {
            state: document.getElementById('profile-state').value || null,
            district: document.getElementById('profile-district').value || null,
            pincode: document.getElementById('profile-pincode').value || null
        }
    };
    
    try {
        showStatus('eligibility-status', 'Finding eligible schemes...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/schemes/eligible`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_profile: userProfile })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayAllEligibleSchemes(data.eligible_schemes || []);
            showStatus('eligibility-status', `Found ${data.eligible_schemes?.length || 0} eligible schemes`, 'success');
        } else {
            showStatus('eligibility-status', `Error: ${data.message || 'Failed to get eligible schemes'}`, 'error');
        }
    } catch (error) {
        showStatus('eligibility-status', `Error: ${error.message}`, 'error');
    }
}

function displayEligibilityResult(result) {
    const container = document.getElementById('eligibility-results');
    
    const eligibleClass = result.is_eligible ? 'eligible' : 'not-eligible';
    const eligibleText = result.is_eligible ? '✅ You are ELIGIBLE' : '❌ You are NOT ELIGIBLE';
    
    container.innerHTML = `
        <div class="eligibility-result ${eligibleClass}">
            <h4>${eligibleText}</h4>
            <p><strong>Scheme:</strong> ${result.scheme_name || 'N/A'}</p>
            <p><strong>Reasoning:</strong> ${result.reasoning || 'No reasoning provided'}</p>
            
            ${result.missing_criteria && result.missing_criteria.length > 0 ? `
                <p><strong>Missing Criteria:</strong></p>
                <ul>
                    ${result.missing_criteria.map(c => `<li>${c}</li>`).join('')}
                </ul>
            ` : ''}
            
            ${result.matched_criteria && result.matched_criteria.length > 0 ? `
                <p><strong>Matched Criteria:</strong></p>
                <ul>
                    ${result.matched_criteria.map(c => `<li>${c}</li>`).join('')}
                </ul>
            ` : ''}
        </div>
    `;
}

function displayAllEligibleSchemes(schemes) {
    const container = document.getElementById('eligibility-results');
    
    if (schemes.length === 0) {
        container.innerHTML = '<p style="color: #6c757d; text-align: center; padding: 20px;">No eligible schemes found. Try updating your profile.</p>';
        return;
    }
    
    container.innerHTML = `
        <h3>You are eligible for ${schemes.length} scheme(s):</h3>
        ${schemes.map(item => `
            <div class="eligibility-result eligible">
                <h4>✅ ${item.scheme.name}</h4>
                <p><strong>Category:</strong> ${item.scheme.category}</p>
                <p><strong>Department:</strong> ${item.scheme.department || 'N/A'}</p>
                <p>${item.scheme.description || ''}</p>
                <p><strong>Why you're eligible:</strong> ${item.eligibility_result.reasoning || 'Meets all criteria'}</p>
                <button onclick="viewSchemeDetails('${item.scheme.scheme_id}')" class="btn btn-primary btn-small">View Full Details</button>
            </div>
        `).join('')}
    `;
}

// Analytics and Impact Tracking
async function recordEvent() {
    if (!authToken) {
        showStatus('analytics-status', 'Please login first', 'error');
        return;
    }
    
    const eventType = document.getElementById('event-type').value;
    
    try {
        showStatus('analytics-status', 'Recording event...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/impact/event`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_type: eventType,
                event_data: {
                    timestamp: new Date().toISOString(),
                    source: 'web_interface'
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('analytics-status', 'Event recorded successfully', 'success');
        } else {
            showStatus('analytics-status', `Error: ${data.message || 'Failed to record event'}`, 'error');
        }
    } catch (error) {
        showStatus('analytics-status', `Error: ${error.message}`, 'error');
    }
}

async function getAnalytics() {
    if (!authToken) {
        showStatus('analytics-status', 'Please login first', 'error');
        return;
    }
    
    try {
        showStatus('analytics-status', 'Loading analytics...', 'info');
        
        const response = await fetch(`${config.apiEndpoint}/impact`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayAnalytics(data);
            showStatus('analytics-status', 'Analytics loaded successfully', 'success');
        } else {
            showStatus('analytics-status', `Error: ${data.message || 'Failed to load analytics'}`, 'error');
        }
    } catch (error) {
        showStatus('analytics-status', `Error: ${error.message}`, 'error');
    }
}

function displayAnalytics(data) {
    const container = document.getElementById('analytics-results');
    
    container.innerHTML = `
        <div class="analytics-card">
            <h4>Impact Metrics</h4>
            <div class="metric">
                <span class="metric-label">Total Events:</span>
                <span class="metric-value">${data.total_events || 0}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Unique Users:</span>
                <span class="metric-value">${data.unique_users || 0}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Schemes Accessed:</span>
                <span class="metric-value">${data.schemes_accessed || 0}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Eligibility Checks:</span>
                <span class="metric-value">${data.eligibility_checks || 0}</span>
            </div>
        </div>
        
        ${data.events && data.events.length > 0 ? `
            <div class="analytics-card">
                <h4>Recent Events</h4>
                ${data.events.slice(0, 10).map(event => `
                    <div class="metric">
                        <span class="metric-label">${event.event_type}</span>
                        <span>${new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
}

// Utility Functions
function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `status-message ${type}`;
    
    // Auto-hide after 5 seconds for success/info messages
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            element.textContent = '';
            element.className = 'status-message';
        }, 5000);
    }
}


// ============================================
// Enhanced UI Functions
// ============================================

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.getElementById('theme-icon');
    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    
    showToast(`Switched to ${newTheme} mode`, 'info');
}

// Load saved theme on page load
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Language Toggle (placeholder)
function toggleLanguage() {
    showToast('Language switcher coming soon!', 'info');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${getToastIcon(type)}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Section Navigation
function showSection(sectionName) {
    // Hide all main sections
    const sections = ['home', 'schemes', 'profile', 'voice'];
    sections.forEach(section => {
        const element = document.getElementById(`${section}-section`);
        if (element) {
            element.style.display = 'none';
        }
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionName}`) {
            link.classList.add('active');
        }
    });
}

// Collapsible Sections
function toggleCollapse(contentId) {
    const content = document.getElementById(contentId);
    const header = event.target.closest('.card-header');
    const icon = header.querySelector('.collapse-icon');
    
    content.classList.toggle('collapsed');
    
    if (icon) {
        icon.style.transform = content.classList.contains('collapsed') 
            ? 'rotate(0deg)' 
            : 'rotate(180deg)';
    }
}

// Auth Tab Switching
function switchAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`${tab}-tab`).classList.add('active');
}

// Loading Overlay
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Voice Recording
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

async function toggleVoiceRecording() {
    if (!isRecording) {
        await startVoiceRecording();
    } else {
        stopVoiceRecording();
    }
}

async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await processVoiceInput(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        const button = document.querySelector('.voice-button');
        const icon = document.getElementById('voice-icon');
        const status = document.getElementById('voice-status');
        
        button.classList.add('recording');
        icon.className = 'fas fa-stop';
        status.textContent = '🎤 Listening... Speak now';
        
        showToast('Voice recording started', 'info');
    } catch (error) {
        showToast('Microphone access denied', 'error');
        console.error('Error accessing microphone:', error);
    }
}

function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        const button = document.querySelector('.voice-button');
        const icon = document.getElementById('voice-icon');
        const status = document.getElementById('voice-status');
        
        button.classList.remove('recording');
        icon.className = 'fas fa-microphone';
        status.textContent = '⏳ Processing your voice...';
        
        showToast('Voice recording stopped', 'success');
    }
}

async function processVoiceInput(audioBlob) {
    const status = document.getElementById('voice-status');
    const transcript = document.getElementById('voice-transcript');
    const response = document.getElementById('voice-response');
    
    try {
        showLoading();
        
        // Placeholder for actual API call
        // In production, send audioBlob to /voice/transcribe endpoint
        
        // Simulated response
        setTimeout(() => {
            hideLoading();
            status.textContent = '✅ Voice processed successfully';
            transcript.innerHTML = '<strong>You said:</strong> "Show me agriculture schemes in Maharashtra"';
            response.innerHTML = '<strong>Response:</strong> I found 15 agriculture schemes available in Maharashtra. Would you like to see them?';
            showToast('Voice processed successfully', 'success');
        }, 2000);
        
    } catch (error) {
        hideLoading();
        status.textContent = '❌ Error processing voice';
        showToast('Error processing voice input', 'error');
        console.error('Voice processing error:', error);
    }
}

// Enhanced scheme display with better cards
function displaySchemes(schemes) {
    const container = document.getElementById('search-results');
    
    if (schemes.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; grid-column: 1/-1;">
                <i class="fas fa-search" style="font-size: 4rem; color: var(--gray-400); margin-bottom: 1rem;"></i>
                <p style="color: var(--text-secondary); font-size: 1.125rem;">No schemes found</p>
                <p style="color: var(--text-tertiary);">Try adjusting your search criteria</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = schemes.map(scheme => `
        <div class="scheme-card">
            <h4>${scheme.name}</h4>
            <p><strong><i class="fas fa-tag"></i> Category:</strong> ${scheme.category}</p>
            <p><strong><i class="fas fa-building"></i> Department:</strong> ${scheme.department || 'N/A'}</p>
            ${scheme.state ? `<p><strong><i class="fas fa-map-marker-alt"></i> State:</strong> ${scheme.state}</p>` : ''}
            <p style="margin-top: 0.75rem;">${scheme.description || 'No description available'}</p>
            <div style="margin-top: 1rem;">
                <span class="badge">${scheme.category}</span>
                ${scheme.state ? `<span class="badge">${scheme.state}</span>` : '<span class="badge">Central</span>'}
            </div>
            <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                <button onclick="viewSchemeDetails('${scheme.scheme_id}')" class="btn btn-primary btn-sm">
                    <i class="fas fa-eye"></i> View Details
                </button>
                <button onclick="selectSchemeForEligibility('${scheme.scheme_id}')" class="btn btn-outline btn-sm">
                    <i class="fas fa-check"></i> Check Eligibility
                </button>
            </div>
        </div>
    `).join('');
}

// Enhanced eligibility result display
function displayEligibilityResult(result) {
    const container = document.getElementById('eligibility-results');
    
    const eligibleClass = result.is_eligible ? 'eligible' : 'not-eligible';
    const eligibleIcon = result.is_eligible ? 'check-circle' : 'times-circle';
    const eligibleText = result.is_eligible ? 'You are ELIGIBLE' : 'You are NOT ELIGIBLE';
    const eligibleColor = result.is_eligible ? 'var(--success)' : 'var(--danger)';
    
    container.innerHTML = `
        <div style="background: ${result.is_eligible ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; 
                    border-left: 4px solid ${eligibleColor}; 
                    padding: 2rem; 
                    border-radius: var(--radius-lg); 
                    margin-top: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <i class="fas fa-${eligibleIcon}" style="font-size: 3rem; color: ${eligibleColor};"></i>
                <h3 style="margin: 0; color: ${eligibleColor};">${eligibleText}</h3>
            </div>
            <p><strong>Scheme:</strong> ${result.scheme_name || 'N/A'}</p>
            <p><strong>Reasoning:</strong> ${result.reasoning || 'No reasoning provided'}</p>
            
            ${result.missing_criteria && result.missing_criteria.length > 0 ? `
                <div style="margin-top: 1rem;">
                    <strong style="color: var(--danger);">Missing Criteria:</strong>
                    <ul style="margin-top: 0.5rem;">
                        ${result.missing_criteria.map(c => `<li>${c}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${result.matched_criteria && result.matched_criteria.length > 0 ? `
                <div style="margin-top: 1rem;">
                    <strong style="color: var(--success);">Matched Criteria:</strong>
                    <ul style="margin-top: 0.5rem;">
                        ${result.matched_criteria.map(c => `<li>${c}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// Update all API calls to use toast notifications
const originalRegister = register;
register = async function() {
    showLoading();
    try {
        await originalRegister.call(this);
    } finally {
        hideLoading();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadAuthState();
    loadTheme();
    
    // Show home section by default
    showSection('home');
    
    // Add smooth scroll to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
        });
    });
});

// Update existing showStatus to use toast
const originalShowStatus = showStatus;
showStatus = function(elementId, message, type) {
    showToast(message, type);
};


// ============================================
// Service Worker Registration (PWA Support)
// ============================================

// Register service worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then((registration) => {
                console.log('Service Worker registered successfully:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('Service Worker update found');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New service worker available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch((error) => {
                console.error('Service Worker registration failed:', error);
            });
    });
    
    // Handle service worker updates
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
            refreshing = true;
            window.location.reload();
        }
    });
}

// Show update notification
function showUpdateNotification() {
    const updateBanner = document.createElement('div');
    updateBanner.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--primary);
        color: white;
        padding: 1rem 2rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-xl);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 1rem;
        animation: slideUp 0.3s ease-out;
    `;
    
    updateBanner.innerHTML = `
        <span>New version available!</span>
        <button onclick="updateServiceWorker()" style="
            background: white;
            color: var(--primary);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            font-weight: 600;
            cursor: pointer;
        ">Update Now</button>
        <button onclick="this.parentElement.remove()" style="
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            font-weight: 600;
            cursor: pointer;
        ">Later</button>
    `;
    
    document.body.appendChild(updateBanner);
}

// Update service worker
function updateServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistration().then((registration) => {
            if (registration && registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
        });
    }
}

// Install prompt for PWA
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button
    showInstallPrompt();
});

function showInstallPrompt() {
    const installBanner = document.createElement('div');
    installBanner.id = 'install-banner';
    installBanner.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-xl);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 1rem;
        animation: slideUp 0.3s ease-out;
        max-width: 90%;
    `;
    
    installBanner.innerHTML = `
        <i class="fas fa-download"></i>
        <span>Install BharatSahayak app for offline access</span>
        <button onclick="installPWA()" style="
            background: white;
            color: var(--primary);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            font-weight: 600;
            cursor: pointer;
        ">Install</button>
        <button onclick="document.getElementById('install-banner').remove()" style="
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            font-weight: 600;
            cursor: pointer;
        ">Not Now</button>
    `;
    
    document.body.appendChild(installBanner);
}

async function installPWA() {
    if (!deferredPrompt) {
        return;
    }
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user's response
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to install prompt: ${outcome}`);
    
    if (outcome === 'accepted') {
        showToast('App installed successfully!', 'success');
    }
    
    // Clear the deferred prompt
    deferredPrompt = null;
    
    // Remove install banner
    const banner = document.getElementById('install-banner');
    if (banner) {
        banner.remove();
    }
}

// Detect if app is running as PWA
function isPWA() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
}

// Show PWA status
if (isPWA()) {
    console.log('Running as PWA');
    // Hide install prompt if already installed
    const installBanner = document.getElementById('install-banner');
    if (installBanner) {
        installBanner.remove();
    }
}

// Online/Offline detection
window.addEventListener('online', () => {
    showToast('You are back online!', 'success');
    console.log('Network: Online');
});

window.addEventListener('offline', () => {
    showToast('You are offline. Some features may be limited.', 'warning');
    console.log('Network: Offline');
});

// Check initial network status
if (!navigator.onLine) {
    showToast('You are currently offline', 'warning');
}

console.log('BharatSahayak PWA initialized successfully');
