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
