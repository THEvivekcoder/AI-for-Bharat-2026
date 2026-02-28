# 🎙️ BharatSahayak Demo Guide

## Quick Start (5 Minutes to Demo-Ready)

### Step 1: Disable Rate Limiting
```bash
python scripts/disable_rate_limiting_for_demo.py
```

### Step 2: Start Server
```bash
uvicorn app.main:app --reload
```

### Step 3: Validate Killer Flow
```bash
python scripts/demo_killer_flow.py
```

If all tests pass → **YOU'RE DEMO READY!** 🎉

## The Killer Flow

**Voice → Hindi Question → Scheme Eligibility → Audio Reply → Impact Recorded**

### What Makes It Killer?

1. **Multilingual Voice Input** - Speak in any Indian language
2. **Automatic Language Detection** - No manual selection needed
3. **RAG-Powered Answers** - Accurate, contextual responses
4. **Audio Output** - Accessibility for low-literacy users
5. **Impact Tracking** - Every interaction measured

### Demo Script

```
DEMO: "Let me show you how a farmer in rural India can access government schemes using just their voice..."

[Open Swagger UI at http://localhost:8000/docs]

1. POST /api/integrated/voice-query
   - Upload audio file (Hindi question about PM-KISAN)
   - Show response with:
     ✓ Transcribed text
     ✓ Detected language (hi)
     ✓ Answer in Hindi
     ✓ Audio response (base64)
     ✓ Session ID for tracking

2. Explain the flow:
   "Behind the scenes:
    - Speech-to-Text transcribed the audio
    - Language detector identified Hindi
    - RAG engine searched our knowledge base
    - Response generated in user's language
    - Text-to-Speech created audio reply
    - Impact tracker recorded the interaction"

3. Show impact:
   GET /api/impact/metrics
   - Show total interactions
   - Show language distribution
   - Show scheme access patterns
```

## API Endpoints for Demo

### Core Flow
- `POST /api/integrated/voice-query` - THE KILLER ENDPOINT
- `POST /api/voice-to-text` - STT only
- `POST /api/ask` - RAG query
- `POST /api/schemes/eligible` - Check eligibility

### Supporting
- `GET /health` - System status
- `GET /api/impact/metrics` - Impact dashboard
- `GET /api/schemes` - Browse schemes

## Test Data

### Sample Questions (Hindi)
1. "PM Kisan yojana kya hai?"
2. "Mujhe kisan yojana ke bare mein bataye"
3. "Kya main PM Kisan ke liye eligible hoon?"

### Sample User Profile
```json
{
  "age": 35,
  "occupation": "farmer",
  "state": "Uttar Pradesh",
  "land_size_acres": 2.5,
  "income_bracket": "below_2_lakh"
}
```

## Demo Talking Points

### Problem Statement
- 60% of rural India has low literacy
- Government schemes exist but are hard to discover
- Language barriers prevent access
- No way to measure impact

### Solution
- Voice-first interface (no reading required)
- Multilingual support (12+ Indian languages)
- AI-powered scheme matching
- Real-time impact tracking

### Technical Highlights
- FastAPI backend (high performance)
- RAG architecture (accurate answers)
- Property-based testing (correctness guaranteed)
- Offline-first PWA (works without internet)

### Impact Metrics
- X users helped
- Y schemes accessed
- Z applications submitted
- Impact across N states

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Restart
uvicorn app.main:app --reload
```

### Rate Limiting Still Active
```bash
# Verify it's disabled
grep "RATE LIMITING DISABLED" app/main.py

# If not, run again
python scripts/disable_rate_limiting_for_demo.py

# Restart server
```

### Audio Not Working
```bash
# Check voice dependencies
python scripts/validate_voice_module.py

# Install if needed
bash install_voice_deps.sh
```

### Database Errors
```bash
# Run migrations
alembic upgrade head

# Seed test data
python scripts/seed_schemes.py
```

## After Demo

### Restore Rate Limiting
```bash
python scripts/disable_rate_limiting_for_demo.py restore
```

### Clean Up Test Data
```bash
# Clear test users
# Clear test interactions
# Reset database if needed
```

## Demo Checklist

Before demo:
- [ ] Rate limiting disabled
- [ ] Server running
- [ ] Killer flow validated
- [ ] Test audio files ready
- [ ] Swagger UI accessible
- [ ] Impact metrics visible
- [ ] Backup plan if internet fails

During demo:
- [ ] Start with problem statement
- [ ] Show voice input
- [ ] Highlight language detection
- [ ] Explain RAG architecture
- [ ] Show impact tracking
- [ ] Answer questions confidently

After demo:
- [ ] Restore rate limiting
- [ ] Note feedback
- [ ] Follow up on questions

## Success Criteria

Demo is successful if:
1. Voice input works smoothly
2. Response is accurate and relevant
3. Audio output plays correctly
4. Impact tracking is visible
5. Audience understands the value

Remember: **One perfect flow beats 100 mediocre features.**
