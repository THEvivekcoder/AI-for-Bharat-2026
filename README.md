# BharatSahayak

Voice-first, multilingual AI assistant designed to democratize access to government services, agricultural guidance, skill development, and healthcare information for rural and semi-urban India.

## Overview

BharatSahayak bridges the digital divide by providing an accessible interface for illiterate and semi-literate populations through natural language voice interactions in Hindi and regional Indian languages.

## Features

- **Voice-First Interaction**: Speech-to-text and text-to-speech in multiple Indian languages
- **Government Scheme Discovery**: Find and apply for relevant government schemes
- **Agricultural Advisory**: Crop recommendations, fertilizer guidance, and market prices
- **Skill Development**: Match users with training programs and employment opportunities
- **Health Information**: Basic health guidance and facility locator
- **Offline Support**: Core features available without internet connectivity
- **Progressive Web App**: Lightweight app for low-end devices (1GB RAM)

## Architecture

- **Backend**: FastAPI on AWS Lambda
- **API Gateway**: AWS API Gateway with Cognito authentication
- **Database**: DynamoDB for NoSQL data, PostgreSQL for relational data
- **Storage**: S3 for voice data and ML models
- **AI**: RAG-powered responses with LLM integration
- **Voice**: Whisper/Vosk for STT, Indic TTS for speech synthesis

## Project Structure

```
bharatsahayak/
├── src/                    # Source code
│   ├── api/               # FastAPI routes and endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Data models and schemas
│   ├── services/          # Domain services
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── property/         # Property-based tests
├── infrastructure/        # Infrastructure as code
│   ├── cloudformation/   # CloudFormation templates
│   └── scripts/          # Deployment scripts
├── data/                  # Data files (gitignored)
├── models/                # ML models (gitignored)
├── template.yaml          # AWS SAM template
├── samconfig.toml         # SAM configuration
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- AWS SAM CLI
- Docker (for local testing)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bharatsahayak
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure AWS credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and region (ap-south-1)
   ```

6. **Create DynamoDB tables**
   ```bash
   # For AWS deployment
   python infrastructure/scripts/create_dynamodb_tables.py dev
   
   # For local DynamoDB (requires DynamoDB Local running on port 8000)
   python infrastructure/scripts/create_dynamodb_tables.py dev http://localhost:8000
   ```

7. **Setup S3 bucket for static content**
   ```bash
   # After deploying the SAM template, setup the folder structure
   python infrastructure/scripts/setup_s3_bucket.py --environment dev --create-sample-structure
   
   # See docs/S3_SETUP.md for detailed information
   ```

## Development

### Local Testing

```bash
# Build the SAM application
sam build

# Start local API
sam local start-api

# Invoke a specific function
sam local invoke FunctionName -e events/event.json
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/property/
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

## Deployment

### Deploy to AWS

```bash
# Build
sam build

# Deploy (first time)
sam deploy --guided

# Deploy (subsequent)
sam deploy

# Deploy to specific environment
sam deploy --parameter-overrides Environment=staging
```

### Validate Template

```bash
sam validate --lint
```

## AWS Resources

After deployment, the following resources are created:

- **API Gateway**: REST API endpoint
- **Lambda Functions**: Serverless compute
- **Cognito User Pool**: User authentication
- **DynamoDB Tables**: 
  - Users (user_id PK, phone_number GSI)
  - Schemes (scheme_id PK, category GSI)
  - UserProfiles (user_id PK)
  - Interactions (user_id PK, timestamp SK)
- **S3 Buckets**: 
  - Voice data (bharatsahayak-voice-data-{env})
  - ML models (bharatsahayak-models-{env})
  - Static content and scheme documents (bharatsahayak-static-content-{env})
- **CloudWatch**: Logs and monitoring

See [docs/S3_SETUP.md](docs/S3_SETUP.md) for S3 bucket configuration details.

## Configuration

### AWS Region

Default region is `ap-south-1` (Mumbai) for optimal latency in India. Configure in `samconfig.toml`.

### Environment Variables

See `.env.example` for all configuration options. Key variables:

- `AWS_REGION`: AWS region for deployment
- `ENVIRONMENT`: dev/staging/prod
- `USER_POOL_ID`: Cognito User Pool ID (from deployment)
- `LLM_API_KEY`: API key for LLM service

## Testing Strategy

The project uses a dual testing approach:

1. **Unit Tests**: Specific examples and edge cases
2. **Property-Based Tests**: Universal properties using Hypothesis

See the design document for detailed testing requirements.

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run code quality checks
4. Submit pull request

## License

[To be determined]

## Support

For issues and questions, please contact the development team.
