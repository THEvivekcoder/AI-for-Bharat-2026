# 🇮🇳 BharatSahayak

> Voice-first, multilingual AI assistant democratizing access to government services for rural India

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20API%20Gateway-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-TBD-green)]()

**BharatSahayak** bridges the digital divide by providing an accessible, voice-first interface for illiterate and semi-literate populations through natural language interactions in 10+ Indian languages.

## 🎯 Problem Statement

Rural and semi-urban populations in India face significant barriers:
- 📚 Low digital literacy and language barriers
- 📝 Complex application processes requiring documentation
- 📡 Limited internet connectivity in remote areas
- ❓ Lack of personalized guidance for scheme eligibility
- 🌊 Information overload without proper filtering

## 💡 Our Solution

An AI-powered assistant that:
- 🎤 Understands voice commands in regional languages
- 🤖 Provides personalized scheme recommendations from 3,400+ government schemes
- 📱 Works offline on low-end devices (1GB RAM)
- 🌾 Offers agricultural advisory and market prices
- 💼 Matches users with skill development and job opportunities

## ✨ Key Features

### 🎤 Voice-First Interface
- Speech-to-text in 10+ Indian languages (Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Malayalam, Punjabi, English)
- Natural text-to-speech with Indian accents
- Automatic language detection
- Conversational AI for natural interactions

### 🏛️ Government Scheme Discovery (3,400+ Schemes)
- Smart search with category and location filters
- Automated eligibility checking based on user profile
- Step-by-step application guidance
- Document requirement checklist
- Save and bookmark schemes

### 🌾 Agricultural Advisory
- Crop recommendations based on soil and climate
- Real-time mandi (market) prices
- Fertilizer and pesticide guidance
- Farm equipment schemes
- Weather-based farming tips

### 💼 Skill Development & Employment
- Skill program matching based on education and interests
- Government job postings search
- Training program recommendations
- Certification tracking

### 🏥 Health Information
- Nearby health facility locator
- Basic symptom checker
- Health scheme eligibility
- Emergency contact information

### 📱 Offline Support
- Progressive Web App (PWA) for low-end devices
- Local data caching for core features
- Background sync when online
- Fast loading even on 2G networks

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- HTML5/CSS3/JavaScript (Modern responsive UI)
- Progressive Web App (PWA) with Service Workers
- IndexedDB for offline data storage
- LocalStorage for session management

**Backend:**
- Python 3.12 on AWS Lambda (Serverless)
- AWS API Gateway (REST API with CORS)
- AWS SAM for Infrastructure as Code

**Data Storage:**
- DynamoDB (12 tables, PAY_PER_REQUEST billing)
- S3 (Voice data, ML models, static content)

**AI/ML Services:**
- AWS Transcribe (Speech-to-Text)
- AWS Polly (Text-to-Speech)
- AWS Translate (Multi-language translation)
- AWS Comprehend (Language detection, NLP)

**Security & Monitoring:**
- JWT-based authentication
- CloudWatch (Logs & Metrics)
- X-Ray (Distributed tracing)

### System Architecture

```
┌─────────────────────────────────────┐
│  User Layer (Mobile/Desktop/PWA)    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Frontend (HTML5/CSS3/JS + PWA)     │
│  • Service Workers (Offline)        │
│  • IndexedDB (Local Cache)          │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  AWS API Gateway                    │
│  • REST API + CORS                  │
│  • Caching (300s TTL)               │
│  • Throttling (50 req/sec)          │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Lambda Functions (20+)             │
│  • Auth, User, Schemes              │
│  • Voice, AI, Agriculture           │
│  • Skills, Health, Analytics        │
└──────┬──────────────────┬───────────┘
       ↓                  ↓
┌──────────────┐   ┌──────────────────┐
│ AWS AI/ML    │   │  Data Layer      │
│ • Transcribe │   │  • DynamoDB (12) │
│ • Polly      │   │  • S3 (3)        │
│ • Translate  │   │  • CloudWatch    │
│ • Comprehend │   │                  │
└──────────────┘   └──────────────────┘
```

## 📁 Project Structure

```
bharatsahayak/
├── src/                           # Backend source code
│   ├── api/                      # Lambda function handlers (20+)
│   │   ├── auth_email_register.py
│   │   ├── auth_email_login.py
│   │   ├── schemes_search.py
│   │   ├── check_eligibility.py
│   │   ├── voice_to_text.py
│   │   ├── text_to_voice.py
│   │   ├── translate_scheme.py
│   │   └── ... (14 more endpoints)
│   ├── core/                     # Business logic
│   │   ├── eligibility.py
│   │   ├── scheme.py
│   │   ├── user.py
│   │   └── voice.py
│   ├── models/                   # Data models
│   ├── services/                 # External service integrations
│   │   ├── transcribe_service.py
│   │   ├── polly_service.py
│   │   ├── translate_service.py
│   │   └── comprehend_service.py
│   └── utils/                    # Utility functions
│
├── modern-ui/                    # Frontend application
│   ├── index.html               # Landing page
│   ├── dashboard.html           # User dashboard
│   ├── search.html              # Scheme search
│   ├── details.html             # Scheme details
│   ├── register.html            # User registration
│   ├── login.html               # User login
│   ├── profile-setup.html       # Profile setup
│   ├── css/                     # Stylesheets
│   └── js/                      # JavaScript
│       ├── app.js               # Main application logic
│       ├── api-client.js        # API wrapper
│       └── schemes-data.js      # 3,400+ schemes data
│
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── property/                # Property-based tests
│
├── infrastructure/               # Infrastructure as Code
│   ├── scripts/                 # Deployment scripts
│   │   ├── create_dynamodb_tables.py
│   │   ├── load_schemes.py
│   │   └── setup_s3_bucket.py
│   └── cloudformation/          # CloudFormation templates
│
├── data/                         # Data files
│   └── updated_data.csv         # 3,400+ government schemes
│
├── docs/                         # Documentation
│   ├── API_DEPLOYMENT_GUIDE.md
│   ├── AWS_SETUP.md
│   ├── DYNAMODB_SETUP.md
│   └── S3_SETUP.md
│
├── template.yaml                 # AWS SAM template (main)
├── samconfig.toml               # SAM configuration
├── requirements.txt             # Python dependencies
├── requirements-lambda.txt      # Lambda layer dependencies
├── deploy-cli.ps1               # Deployment script
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- AWS Account with CLI configured
- AWS SAM CLI (optional, for advanced deployment)
- Node.js (for local frontend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bharatsahayak
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS credentials**
   ```bash
   aws configure
   # Enter: Access Key, Secret Key, Region (ap-south-1)
   ```

### Deployment

#### Option 1: Automated Deployment (Recommended)

```powershell
# Windows PowerShell
.\deploy-cli.ps1
```

```bash
# Linux/Mac
./deploy-cli.sh
```

#### Option 2: SAM CLI Deployment

```bash
# Build
sam build

# Deploy (first time - interactive)
sam deploy --guided

# Deploy (subsequent)
sam deploy
```

#### Option 3: Manual Deployment

```powershell
# Create deployment package
.\create-package.ps1

# Then upload to AWS Console:
# https://console.aws.amazon.com/cloudformation/
```

### Post-Deployment Setup

1. **Get API Endpoint**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name bharatsahayak-dev \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text
   ```

2. **Update Frontend Configuration**
   ```javascript
   // modern-ui/config.js
   window.CONFIG = {
     api: {
       baseURL: 'YOUR_API_ENDPOINT_HERE'
     }
   };
   ```

3. **Load Schemes Data**
   ```bash
   python scripts/load_schemes.py
   ```

4. **Test the Application**
   ```bash
   # Test backend
   python test_backend_endpoints.py
   
   # Test frontend (open in browser)
   modern-ui/index.html
   ```

## 🧪 Development

### Local Development

#### Frontend Development Server

```bash
cd modern-ui
node server.js
# Open http://localhost:3000
```

#### Local API Testing

```bash
# Build SAM application
sam build

# Start local API
sam local start-api --port 3001

# Test specific function
sam local invoke FunctionName -e events/sample-request.json
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/property/          # Property-based tests

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

### Testing Individual Endpoints

```bash
# Test schemes endpoint
curl https://YOUR_API_ENDPOINT/schemes?limit=5

# Test with authentication
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://YOUR_API_ENDPOINT/user/profile
```

## 📊 AWS Resources

After deployment, the following resources are created:

### Compute & API
- **API Gateway**: REST API with CORS, caching, and throttling
- **Lambda Functions**: 20+ serverless functions
  - Authentication (register, login, OTP)
  - User management (profile, dashboard, stats)
  - Schemes (search, details, eligibility)
  - Voice services (STT, TTS, translation)
  - Agriculture (crop advice, market prices)
  - Skills & Jobs (matching, search)
  - Health (facilities, symptoms)
  - Analytics (impact tracking)

### Data Storage
- **DynamoDB Tables** (12 tables, PAY_PER_REQUEST):
  - `bharatsahayak-users-{env}` - User accounts
  - `bharatsahayak-schemes-{env}` - 3,400+ government schemes
  - `bharatsahayak-user-profiles-{env}` - User profiles
  - `bharatsahayak-saved-schemes-{env}` - Bookmarked schemes
  - `bharatsahayak-interactions-{env}` - User interactions
  - `bharatsahayak-farm-profiles-{env}` - Farm data
  - `bharatsahayak-mandi-prices-{env}` - Market prices
  - `bharatsahayak-skill-programs-{env}` - Skill programs
  - `bharatsahayak-job-postings-{env}` - Job listings
  - `bharatsahayak-health-facilities-{env}` - Health centers
  - `bharatsahayak-translation-cache-{env}` - Translation cache
  - `bharatsahayak-conversation-sessions-{env}` - Chat sessions

- **S3 Buckets** (3 buckets):
  - `bharatsahayak-voice-{account}-{env}` - Voice recordings
  - `bharatsahayak-models-{account}-{env}` - ML models
  - `bharatsahayak-static-{account}-{env}` - Static content & documents

### Monitoring & Security
- **CloudWatch**: Logs, metrics, and alarms
- **X-Ray**: Distributed tracing (production only)
- **IAM Roles**: Least-privilege access for Lambda functions

### Cost Estimate

**AWS Free Tier (First 12 months):**
- Lambda: 1M requests/month FREE
- API Gateway: 1M requests/month FREE
- DynamoDB: 25GB storage FREE

**After Free Tier:**
- Development: ~$5-10/month
- Production: ~$120/month (1M requests)
- Scalable: ~$500/month (10M requests)

See [docs/AWS_SETUP.md](docs/AWS_SETUP.md) for detailed resource configuration.

## 🔧 Configuration

### Environment Variables

Key configuration in `template.yaml`:

```yaml
Environment:
  Variables:
    ENVIRONMENT: dev/staging/prod
    JWT_SECRET: your-secret-key
    LOG_LEVEL: INFO/DEBUG
```

### AWS Region

Default: `ap-south-1` (Mumbai) for optimal latency in India.

Configure in `samconfig.toml`:
```toml
[default.deploy.parameters]
region = "ap-south-1"
```

### Frontend Configuration

Update `modern-ui/config.js` after deployment:

```javascript
window.CONFIG = {
  api: {
    baseURL: 'https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/dev'
  }
};
```

## 📚 API Endpoints

### Authentication
- `POST /auth/email/register` - Register new user
- `POST /auth/email/login` - Login user
- `POST /auth/verify-otp` - Verify OTP (if enabled)

### User Management
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update profile
- `GET /user/stats` - Get user statistics
- `GET /dashboard/data` - Get dashboard data

### Schemes
- `GET /schemes` - List all schemes
- `GET /schemes/search` - Search schemes
- `GET /schemes/{id}` - Get scheme details
- `GET /schemes/eligible` - Get eligible schemes
- `POST /schemes/check-eligibility` - Check eligibility
- `POST /schemes/save` - Save/bookmark scheme

### Voice & AI
- `POST /voice-to-text` - Speech to text
- `POST /voice/synthesize` - Text to speech
- `POST /voice/detect-language` - Detect language
- `POST /translate/scheme` - Translate scheme
- `POST /conversational-query` - AI chat

### Agriculture
- `GET /crop-advice` - Get crop recommendations
- `GET /market-prices` - Get mandi prices

### Skills & Jobs
- `POST /skills/match` - Match skill programs
- `GET /jobs` - Search jobs

### Health
- `GET /health/facilities` - Find health facilities
- `GET /health-check` - API health check

### Analytics
- `POST /impact/event` - Record impact event
- `GET /impact` - Get impact analytics

See [docs/API_DEPLOYMENT_GUIDE.md](docs/API_DEPLOYMENT_GUIDE.md) for detailed API documentation.

## 🧪 Testing Strategy

The project uses comprehensive testing:

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Test API endpoints end-to-end
   - Test AWS service integrations
   - Use test DynamoDB tables

3. **Property-Based Tests** (`tests/property/`)
   - Test universal properties using Hypothesis
   - Generate random test cases
   - Find edge cases automatically

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/property/

# With coverage
pytest --cov=src --cov-report=html

# Specific file
pytest tests/unit/test_eligibility.py

# Specific test
pytest tests/unit/test_eligibility.py::test_check_age_eligibility
```

### Test Coverage

Current coverage: ~80%

View detailed report:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## 🐛 Troubleshooting

### Common Issues

**"AWS CLI not found"**
```bash
# Install AWS CLI
# Windows: https://awscli.amazonaws.com/AWSCLIV2.msi
# Mac: brew install awscli
# Linux: pip install awscli
```

**"Credentials not configured"**
```bash
aws configure
# Enter: Access Key, Secret Key, Region (ap-south-1)
```

**"Stack already exists"**
```bash
# Delete existing stack
aws cloudformation delete-stack --stack-name bharatsahayak-dev
# Wait 5 minutes, then redeploy
```

**"Bucket name already taken"**
```bash
# Edit deploy-cli.ps1
# Change BUCKET_NAME to something unique
```

**"Lambda timeout"**
```bash
# Increase timeout in template.yaml
Timeout: 60  # seconds
```

**"CORS error in frontend"**
```bash
# Verify API Gateway CORS configuration
# Check modern-ui/config.js has correct API endpoint
```

### Debugging

**View Lambda Logs:**
```bash
# Real-time logs
aws logs tail /aws/lambda/bharatsahayak-schemes-search-dev --follow

# Recent logs
aws logs tail /aws/lambda/bharatsahayak-schemes-search-dev --since 1h
```

**Test API Endpoint:**
```bash
# Health check
curl https://YOUR_API_ENDPOINT/health-check

# List schemes
curl https://YOUR_API_ENDPOINT/schemes?limit=5

# With authentication
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://YOUR_API_ENDPOINT/user/profile
```

**Check CloudFormation Stack:**
```bash
# Stack status
aws cloudformation describe-stacks --stack-name bharatsahayak-dev

# Stack events
aws cloudformation describe-stack-events --stack-name bharatsahayak-dev
```

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Write tests for new features
   - Follow code style guidelines
   - Update documentation
4. **Run tests and quality checks**
   ```bash
   pytest
   black src/ tests/
   flake8 src/ tests/
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting
- Use isort for import sorting
- Add type hints where possible
- Write docstrings for functions and classes

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## 📄 License

[To be determined]

## 🙏 Acknowledgments

- Government of India for open data on schemes
- AWS for cloud infrastructure
- Open source community for tools and libraries

## 📞 Support & Contact

### Documentation
- [Quick Start Guide](docs/QUICK_START.md)
- [API Documentation](docs/API_DEPLOYMENT_GUIDE.md)
- [AWS Setup Guide](docs/AWS_SETUP.md)
- [DynamoDB Setup](docs/DYNAMODB_SETUP.md)
- [S3 Configuration](docs/S3_SETUP.md)


### Project Links
- **Live Demo**:(https://bharatsahayak-static-390402557080-dev.s3.us-east-1.amazonaws.com/app/index.html)
- **Video Demo**: (https://drive.google.com/file/d/1X49PowTeTn4PlNsx34utxii8aj4UrXtR/view?usp=sharing)

## 🎯 Project Status

- ✅ Backend: 20+ Lambda functions deployed
- ✅ Frontend: Modern responsive UI with PWA
- ✅ Data: 3,400+ government schemes loaded
- ✅ AI Services: Voice, translation, NLP integrated
- ✅ Testing: Unit, integration, property-based tests
- ✅ Documentation: Comprehensive guides available
- 🚀 Status: **Production Ready**

## 📊 Impact Goals

- 🎯 Reach 10 million rural users in 2 years
- 📈 Increase scheme awareness by 50%
- ⚡ Reduce application time by 70%
- 👥 Create 1,000+ rural digital champions
- 🤝 Partner with 100+ NGOs

---

**Made with ❤️ for Rural India** 🇮🇳

*Empowering citizens through AI and voice technology*
