
# 🇮🇳 BharatSahayak
## Voice-First AI Public Assistant for Communities, Access & Public Impact

BharatSahayak is a multilingual, voice-enabled AI civic assistant designed to bridge the digital divide in rural and semi-urban India. It provides simple, voice-first access to **government schemes, agricultural guidance, healthcare information, and skill opportunities** — even in **low-bandwidth and offline environments**.

---

## 🌍 Problem

Millions of citizens in India cannot access public services due to:

- Illiteracy and language barriers  
- Lack of awareness about government schemes  
- Poor internet connectivity  
- Fragmented access to jobs, healthcare, and agriculture information  
- Complex government processes and information  

**BharatSahayak democratizes access using AI + Voice + Local Language.**

---

## 🚀 Features

- 🎤 Voice-first interaction for illiterate and semi-literate users  
- 🌐 Multilingual support (Hindi + regional languages)  
- 📡 Low-bandwidth and offline mode support  
- 🧠 AI-powered conversational assistant  
- 🏛 Government scheme discovery and eligibility checker  
- 🌾 Farmer advisory (crop, fertilizer, mandi prices)  
- 🎓 Skill and job recommendation system  
- 🏥 Health guidance and nearby facility locator  
- 📊 Social impact analytics  
- 🔐 Privacy and secure design  

---

## 🧠 AI Architecture

- **LLM:** LLaMA / Mistral / GPT  
- **RAG:** Retrieval-Augmented Generation for contextual answers  
- **Vector DB:** FAISS  
- **Speech-to-Text:** Whisper / Vosk  
- **Text-to-Speech:** Indic TTS / Coqui  
- **Indic NLP:** Bhashini / IndicTrans  

---

## 🏗 System Architecture


Supports **Cloud + Offline Edge Deployment**

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| POST `/api/ask` | Main AI query |
| GET `/api/schemes` | Government schemes |
| POST `/api/schemes/check-eligibility` | Eligibility checker |
| GET `/api/farmer/market-price` | Mandi prices |
| POST `/api/farmer/crop-advice` | Crop recommendations |
| GET `/api/skills` | Skill programs |
| POST `/api/health/check` | Health guidance |
| POST `/api/voice-to-text` | Speech to Text |
| POST `/api/text-to-voice` | Text to Speech |
| GET `/api/impact` | Social impact metrics |

---

## 🧩 Core Modules

### Government Scheme Assistant
- Discover government schemes
- Check eligibility
- Step-by-step application guidance

### Farmer AI Advisor
- Crop recommendation
- Fertilizer guidance
- Real-time mandi price

### Skill & Job Assistant
- Skill development matching
- Government job discovery
- Career suggestions

### Health Assistant
- Symptom-based guidance
- Nearby health facility locator
- Health scheme awareness

### Voice & Language Engine
- Voice-first interaction
- Multilingual support
- Designed for low literacy users

---

## 📊 Impact Metrics

The system tracks:

- Users served  
- Queries resolved  
- Schemes accessed  
- Farmers assisted  
- Jobs discovered  
- Skill enrollments  
- Rural adoption rate  
- Languages used  

---

## 🔐 Security & Privacy

- Encrypted communication (TLS)  
- Encrypted personal data (AES-256)  
- Role-based access control  
- PII anonymization in analytics  
- Data deletion support  

---

## 📶 Offline & Low-Bandwidth Support

- Progressive Web App (PWA)  
- SQLite offline cache  
- Data compression (<100KB per query)  
- Works on low-end smartphones (1GB RAM)  

---

## 🧪 Testing

- Unit testing  
- Property-based testing  
- Integration testing  
- Load and performance testing  
- Offline and low-bandwidth testing  
- Security and privacy testing  

---

## ⚙️ Tech Stack

**Backend**
- FastAPI (Python)
- LangChain / LlamaIndex

**AI**
- LLaMA / Mistral / GPT
- Whisper STT
- Indic TTS
- Sentence Transformers

**Frontend**
- React / Next.js
- Progressive Web App

**Database**
- PostgreSQL
- SQLite (offline)
- Redis Cache
- FAISS Vector DB

**Cloud**
- AWS / GCP / Azure

---

## 🚀 Deployment

Supports:

- Cloud deployment  
- Edge/offline deployment  
- PWA install (no app store needed)  

---

## 🎯 Innovation

- Voice-first AI for illiterate users  
- Offline-capable public service AI  
- Multilingual conversational assistant  
- Unified platform for schemes + jobs + health + agriculture  
- Personalized AI recommendations  
- Designed for real rural deployment  

---

## 📌 Future Scope

- WhatsApp AI assistant  
- IVR voice call system  
- SMS-based query support  
- Women-focused health and safety features  
- Tribal and regional dialect support  
- AI-based scheme auto-application assistant  

---

## 🤝 Contributing

Contributions are welcome. Feel free to open issues or submit pull requests.

---

## 📜 License

MIT License

---

## 👨‍💻 Author

**Vivek Kumar**  
AI for Bharat | Social Impact Project
