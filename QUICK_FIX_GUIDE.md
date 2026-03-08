# Quick Fix Guide - Complete All Pages in 30 Minutes

## What's Done ✅

1. **api-client.js** - Fully working, all API methods available
2. **login.html** - Complete backend integration
3. **dashboard.html** - Complete backend integration  
4. **schemes.html** - Complete backend integration with search, filters, pagination

## What Needs Fixing ⏳

7 pages need backend integration. Here's the fastest way to fix them all:

---

## 1. eligible-schemes.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
window.addEventListener('api-ready', async function() {
    try {
        showLoading();
        const result = await api.getEligibleSchemes();
        
        if (result.success) {
            const schemes = result.data.eligible_schemes || [];
            const container = document.querySelector('[style*="grid-template-columns: repeat(auto-fill"]');
            
            if (schemes.length === 0) {
                container.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 4rem;">
                        <i class="fas fa-inbox" style="font-size: 4rem; color: #9CA3AF;"></i>
                        <h3>No Eligible Schemes Found</h3>
                        <p>Complete your profile to find schemes</p>
                        <button onclick="window.location.href='profile-setup.html'" class="btn btn-primary">
                            Complete Profile
                        </button>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = schemes.map(scheme => `
                <div class="glass-effect hover-lift" style="padding: 2rem; border-radius: 20px; border-left: 5px solid #10B981;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <span style="background: linear-gradient(135deg, #10B981, #059669); color: white; padding: 0.5rem 1rem; border-radius: 10px; font-size: 0.85rem; font-weight: 600;">
                            ${scheme.category}
                        </span>
                        <div style="background: rgba(16, 185, 129, 0.1); color: #10B981; padding: 0.5rem 1rem; border-radius: 10px; font-weight: 600;">
                            ${Math.round(scheme.relevance_score * 100)}% Match
                        </div>
                    </div>
                    <h4 class="text-green" style="font-size: 1.5rem; margin-bottom: 0.75rem;">${scheme.name}</h4>
                    <p style="opacity: 0.9; margin-bottom: 1rem;">${scheme.description}</p>
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: #10B981;">Why you're eligible:</div>
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            ${scheme.eligibility_explanation.reasoning.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                    <div style="display: flex; gap: 0.75rem;">
                        <button class="btn btn-primary btn-sm" onclick="window.location.href='scheme-details.html?id=${scheme.scheme_id}'" style="flex: 1;">
                            View Details
                        </button>
                        <button class="btn btn-outline btn-sm" onclick="window.open('${scheme.application_url}', '_blank')" style="flex: 1;">
                            Apply Now
                        </button>
                    </div>
                </div>
            `).join('');
            
            // Update count
            document.querySelector('[style*="font-size: 1.5rem"]').textContent = schemes.length;
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
});

function showLoading() {
    document.body.style.cursor = 'wait';
}

function hideLoading() {
    document.body.style.cursor = 'default';
}
</script>
```

---

## 2. scheme-details.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
window.addEventListener('api-ready', async function() {
    const urlParams = new URLSearchParams(window.location.search);
    const schemeId = urlParams.get('id');
    
    if (!schemeId) {
        alert('Invalid scheme ID');
        window.location.href = 'schemes.html';
        return;
    }
    
    try {
        const result = await api.getSchemeDetails(schemeId);
        
        if (result.success) {
            const scheme = result.data;
            
            // Update page title
            document.title = `${scheme.name} - BharatSahayak`;
            
            // Find and update elements (adjust selectors based on your HTML)
            const nameEl = document.querySelector('h1');
            if (nameEl) nameEl.textContent = scheme.name;
            
            const descEl = document.querySelector('p');
            if (descEl) descEl.textContent = scheme.description;
            
            // Add benefits
            const benefitsContainer = document.querySelector('#benefits-list') || document.createElement('ul');
            benefitsContainer.innerHTML = scheme.benefits.map(b => `<li>${b}</li>`).join('');
            
            // Add eligibility
            const eligibilityContainer = document.querySelector('#eligibility-list') || document.createElement('ul');
            const criteria = scheme.eligibility_criteria;
            let eligibilityHTML = '';
            if (criteria.age_min || criteria.age_max) {
                eligibilityHTML += `<li>Age: ${criteria.age_min || 0} - ${criteria.age_max || 'No limit'} years</li>`;
            }
            if (criteria.income_max) {
                eligibilityHTML += `<li>Income: Up to ₹${criteria.income_max} per year</li>`;
            }
            eligibilityContainer.innerHTML = eligibilityHTML;
            
            // Add documents
            const docsContainer = document.querySelector('#documents-list') || document.createElement('ul');
            docsContainer.innerHTML = scheme.required_documents.map(d => `<li>${d}</li>`).join('');
            
            // Add application process
            const processContainer = document.querySelector('#process-list') || document.createElement('ol');
            processContainer.innerHTML = scheme.application_process.map(s => `<li>${s}</li>`).join('');
            
            // Set apply button
            const applyBtn = document.querySelector('#apply-button') || document.querySelector('button');
            if (applyBtn && scheme.application_url) {
                applyBtn.onclick = () => window.open(scheme.application_url, '_blank');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to load scheme details');
    }
});
</script>
```

---

## 3. profile.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
window.addEventListener('api-ready', async function() {
    try {
        const result = await api.getUserProfile();
        
        if (result.success) {
            const profile = result.data;
            
            // Update profile fields (adjust selectors based on your HTML)
            const updateText = (selector, value) => {
                const el = document.querySelector(selector);
                if (el) el.textContent = value || 'N/A';
            };
            
            updateText('h1', profile.name || 'User');
            updateText('[style*="phone"]', profile.phone_number);
            
            // Find and update age, gender, education, etc.
            const fields = document.querySelectorAll('[style*="font-size: 1.1rem"]');
            if (fields[0]) fields[0].textContent = profile.age || 'N/A';
            if (fields[1]) fields[1].textContent = profile.gender || 'N/A';
            if (fields[2]) fields[2].textContent = profile.education_level || 'N/A';
            if (fields[3]) fields[3].textContent = profile.occupation || 'N/A';
            if (fields[4]) fields[4].textContent = profile.income_bracket || 'N/A';
            if (fields[5]) fields[5].textContent = 
                `${profile.location.district}, ${profile.location.state} - ${profile.location.pincode}`;
        }
    } catch (error) {
        console.error('Error:', error);
    }
});

function editProfile() {
    window.location.href = 'profile-setup.html';
}
</script>
```

---

## 4. profile-setup.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
async function saveProfile() {
    try {
        const profileData = {
            age: parseInt(document.getElementById('profile-age').value),
            gender: document.getElementById('profile-gender').value,
            education_level: document.getElementById('profile-education').value,
            occupation: document.getElementById('profile-occupation')?.value,
            income_bracket: document.getElementById('profile-income')?.value,
            household_size: parseInt(document.getElementById('profile-household')?.value || 1),
            location: {
                state: document.getElementById('profile-state').value,
                district: document.getElementById('profile-district').value,
                pincode: document.getElementById('profile-pincode').value
            },
            preferences: {
                notification_enabled: true,
                preferred_categories: []
            }
        };
        
        const result = await api.updateUserProfile(profileData);
        
        if (result.success) {
            alert('Profile updated successfully!');
            window.location.href = 'dashboard.html';
        } else {
            alert('Failed to update profile: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to update profile');
    }
}

function skipSetup() {
    window.location.href = 'dashboard.html';
}
</script>
```

---

## 5. voice-assistant.html (5 minutes)

**Replace the existing script section with:**
```html
<script src="api-client.js"></script>
<script>
let isListening = false;
let selectedLanguage = 'hi';
let mediaRecorder = null;
let audioChunks = [];

async function toggleVoice() {
    const button = document.getElementById('voice-button');
    const icon = document.getElementById('voice-icon');
    const status = document.getElementById('voice-status');
    const rings = document.getElementById('voice-rings');
    
    if (!isListening) {
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
            isListening = true;
            
            button.classList.add('active');
            icon.className = 'fas fa-stop';
            status.textContent = 'Listening... Speak now';
            rings.style.display = 'block';
            
        } catch (error) {
            alert('Microphone access denied');
        }
    } else {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        isListening = false;
        button.classList.remove('active');
        icon.className = 'fas fa-microphone';
        status.textContent = 'Processing...';
        rings.style.display = 'none';
    }
}

async function processVoiceInput(audioBlob) {
    const reader = new FileReader();
    reader.onloadend = async () => {
        const base64Audio = reader.result.split(',')[1];
        
        try {
            const result = await api.voiceToText(base64Audio, selectedLanguage);
            
            if (result.success) {
                const transcript = result.data.text;
                document.getElementById('transcript-box').style.display = 'block';
                document.getElementById('transcript-text').textContent = transcript;
                
                await getConversationalResponse(transcript);
            } else {
                alert('Voice processing failed: ' + result.error);
            }
        } catch (error) {
            alert('Voice processing failed');
        }
    };
    reader.readAsDataURL(audioBlob);
}

async function getConversationalResponse(query) {
    try {
        const result = await api.conversationalQuery(query, selectedLanguage);
        
        if (result.success) {
            document.getElementById('response-box').style.display = 'block';
            document.getElementById('response-text').textContent = result.data.answer;
        } else {
            document.getElementById('response-box').style.display = 'block';
            document.getElementById('response-text').textContent = 'Sorry, I could not process your request.';
        }
    } catch (error) {
        document.getElementById('response-box').style.display = 'block';
        document.getElementById('response-text').textContent = 'Sorry, there was an error.';
    }
    
    document.getElementById('voice-status').textContent = 'Tap the microphone to start speaking';
}

function selectLanguage(lang) {
    selectedLanguage = lang;
    document.querySelectorAll('.language-chip').forEach(chip => {
        chip.classList.remove('active');
    });
    event.target.classList.add('active');
}

function useSuggestion(text) {
    document.getElementById('transcript-box').style.display = 'block';
    document.getElementById('transcript-text').textContent = text;
    getConversationalResponse(text);
}
</script>
```

---

## 6. agriculture.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
window.addEventListener('api-ready', async function() {
    await loadCropAdvice();
    await loadMarketPrices();
});

async function loadCropAdvice() {
    try {
        const profileResult = await api.getUserProfile();
        if (!profileResult.success) return;
        
        const location = profileResult.data.location;
        const month = new Date().getMonth() + 1;
        const season = (month >= 6 && month <= 10) ? 'kharif' : (month >= 11 || month <= 3) ? 'rabi' : 'zaid';
        
        const result = await api.getCropAdvice(location.state, season);
        
        if (result.success && result.data.recommendations) {
            const container = document.querySelector('[style*="grid-template-columns"]') || document.body;
            const html = result.data.recommendations.map(rec => `
                <div class="glass-effect" style="padding: 2rem; border-radius: 20px; border-left: 5px solid #10B981;">
                    <h4 class="text-green" style="font-size: 1.5rem; margin-bottom: 1rem;">${rec.crop_name}</h4>
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                        <span style="background: rgba(16, 185, 129, 0.1); padding: 0.5rem 1rem; border-radius: 8px;">
                            ${Math.round(rec.suitability_score * 100)}% Match
                        </span>
                        <span style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem 1rem; border-radius: 8px;">
                            ${rec.duration_days} days
                        </span>
                    </div>
                    <p style="margin-bottom: 1rem;">${rec.reasoning}</p>
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 10px;">
                        <div><strong>Expected Yield:</strong> ${rec.expected_yield}</div>
                        <div><strong>Estimated Profit:</strong> ${rec.estimated_profit}</div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading crop advice:', error);
    }
}

async function loadMarketPrices() {
    try {
        const profileResult = await api.getUserProfile();
        if (!profileResult.success) return;
        
        const location = profileResult.data.location;
        const crops = ['wheat', 'rice', 'soybean', 'cotton'];
        
        for (const crop of crops) {
            const result = await api.getMarketPrices(location.state, crop);
            if (result.success && result.data.prices && result.data.prices.length > 0) {
                const price = result.data.prices[0];
                console.log(`${crop}: ₹${price.price_per_quintal}/quintal at ${price.mandi_name}`);
            }
        }
    } catch (error) {
        console.error('Error loading market prices:', error);
    }
}
</script>
```

---

## 7. settings.html (5 minutes)

**Add before `</body>`:**
```html
<script src="api-client.js"></script>
<script>
window.addEventListener('api-ready', async function() {
    try {
        const result = await api.getUserProfile();
        if (result.success) {
            const profile = result.data;
            
            // Load language
            const langSelect = document.getElementById('language-select') || 
                              document.querySelector('select');
            if (langSelect && profile.language) {
                langSelect.value = profile.language;
            }
            
            // Load notifications
            const notifToggle = document.getElementById('notifications-enabled') || 
                               document.querySelector('input[type="checkbox"]');
            if (notifToggle && profile.preferences) {
                notifToggle.checked = profile.preferences.notification_enabled !== false;
            }
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
});

async function saveSettings() {
    try {
        const langSelect = document.getElementById('language-select') || 
                          document.querySelector('select');
        const notifToggle = document.getElementById('notifications-enabled') || 
                           document.querySelector('input[type="checkbox"]');
        
        const settings = {
            language: langSelect?.value || 'hi',
            preferences: {
                notification_enabled: notifToggle?.checked !== false
            }
        };
        
        const result = await api.updateUserProfile(settings);
        
        if (result.success) {
            alert('Settings saved successfully!');
        } else {
            alert('Failed to save settings: ' + result.error);
        }
    } catch (error) {
        alert('Failed to save settings');
    }
}
</script>
```

---

## Testing Each Page

After adding the code to each page:

1. Open the page in browser
2. Open Developer Console (F12)
3. Check for errors
4. Verify API calls in Network tab
5. Test functionality

## Common Issues

**Issue:** "api is not defined"
**Fix:** Make sure `<script src="api-client.js"></script>` is added BEFORE your custom script

**Issue:** "API not initialized"
**Fix:** Wrap your code in `window.addEventListener('api-ready', function() { ... })`

**Issue:** "Authentication required"
**Fix:** User needs to login first. Redirect to login.html

**Issue:** Elements not found
**Fix:** Adjust the selectors (getElementById, querySelector) to match your actual HTML

## Done!

After completing all 7 pages, your entire frontend will be integrated with the backend. No more static data!

**Total Time:** ~30-35 minutes
**Result:** Fully functional application with real backend integration
