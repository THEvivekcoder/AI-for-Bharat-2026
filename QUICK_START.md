# BharatSahayak - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Checklist
- [ ] Python 3.11 installed
- [ ] AWS Account created
- [ ] AWS CLI installed
- [ ] AWS SAM CLI installed

---

## Step 1: Install Dependencies (2 minutes)

```bash
# Clone and enter project
cd BharatSahayak

# Install Python packages
make install

# Verify installation
make test-unit
```

**Expected:** All unit tests should pass ✅

---

## Step 2: Configure AWS (3 minutes)

```bash
# Configure AWS credentials
aws configure
# Enter your: Access Key, Secret Key, Region (us-east-1), Format (json)

# Verify AWS connection
aws sts get-caller-identity
```

---

## Step 3: Set Environment Variables (2 minutes)

```bash
# Copy template
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
python -c "import base64, os; print('ENCRYPTION_KEY=' + base64.b64encode(os.urandom(32)).decode())"

# Edit .env and paste the generated keys
# Also set: AWS_REGION=us-east-1, AWS_ACCOUNT_ID=your-account-id
```

---

## Step 4: Deploy to AWS (10 minutes)

```bash
# One command to deploy everything!
make deploy-all
```

This will:
1. ✅ Create DynamoDB tables
2. ✅ Create S3 buckets
3. ✅ Deploy Lambda functions
4. ✅ Set up API Gateway
5. ✅ Load sample schemes
6. ✅ Deploy frontend

**Note:** You'll need to manually create Cognito User Pool (instructions will be shown)

---

## Step 5: Test Your Deployment (2 minutes)

```bash
# Get your API URL
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# Test the API
curl YOUR_API_URL/schemes?category=agriculture

# Open frontend
# URL: http://bharatsahayak-frontend.s3-website-us-east-1.amazonaws.com
```

---

## 🎯 Common Commands

### Development
```bash
make test              # Run all tests
make test-unit         # Run unit tests only
make coverage          # Generate coverage report
make lint              # Check code quality
```

### Deployment
```bash
make setup-aws         # Create AWS resources
make deploy-lambda     # Deploy Lambda functions
make deploy-frontend   # Deploy web interface
make load-data         # Load sample schemes
make deploy-all        # Deploy everything
```

### Monitoring
```bash
make logs              # View Lambda logs
aws dynamodb scan --table-name BharatSahayak-Schemes --max-items 5
```

### Cleanup
```bash
make clean             # Clean build artifacts
make destroy           # Delete all AWS resources (CAUTION!)
```

---

## 📁 Project Structure

```
BharatSahayak/
├── src/                    # Source code
│   ├── api/               # Lambda function handlers
│   ├── core/              # Business logic
│   ├── models/            # Data models
│   └── utils/             # Utilities
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── property/         # Property-based tests
│   └── integration/      # Integration tests
├── frontend/              # Web interface
├── scripts/               # Deployment scripts
├── docs/                  # Documentation
├── template.yaml          # SAM template
├── Makefile              # Automation commands
└── .env                  # Configuration (create this)
```

---

## 🔧 Troubleshooting

### "AWS CLI not found"
```bash
# Windows: Download from https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: pip install awscli
```

### "SAM CLI not found"
```bash
# Windows: Download from AWS SAM docs
# Mac: brew install aws-sam-cli
# Linux: Follow AWS SAM installation guide
```

### "Tests failing"
```bash
# Install missing dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run specific test
python -m pytest tests/unit/test_eligibility_checker.py -v
```

### "DynamoDB table already exists"
```bash
# This is OK - the table was created previously
# Continue with deployment
```

### "Cognito not configured"
```bash
# Create User Pool manually:
aws cognito-idp create-user-pool \
    --pool-name BharatSahayak-Users \
    --username-attributes phone_number \
    --region us-east-1

# Then create app client and update .env
```

---

## 📊 What's Included

### ✅ Implemented Features
- User authentication (Cognito + OTP)
- Profile management
- Government scheme database (8 sample schemes)
- Scheme search and filtering
- Eligibility checking engine
- Personalized recommendations
- Impact tracking and analytics
- Web interface
- REST API
- 313 passing tests

### 🔮 Optional Features (Not Yet Implemented)
- Voice interface (speech-to-text/text-to-speech)
- Multilingual translation
- Agricultural advisory
- Skill development matching
- Health advisory
- RAG-based conversational AI
- Offline PWA features

---

## 📚 Documentation

- **DEPLOYMENT_CHECKLIST.md** - Detailed deployment guide
- **PROJECT_STATUS.md** - Current project status
- **README.md** - Project overview
- **docs/** - API documentation

---

## 🎓 Learning Resources

### AWS Services Used
- **Lambda** - Serverless functions
- **API Gateway** - REST API
- **DynamoDB** - NoSQL database
- **S3** - Object storage
- **Cognito** - User authentication
- **CloudWatch** - Logging and monitoring

### Key Technologies
- **Python 3.11** - Backend language
- **FastAPI** - API framework
- **Pydantic** - Data validation
- **Boto3** - AWS SDK
- **Pytest** - Testing framework
- **Hypothesis** - Property-based testing

---

## 💡 Tips

1. **Start small:** Deploy to dev environment first
2. **Test locally:** Use `make test` before deploying
3. **Monitor costs:** Check AWS billing dashboard regularly
4. **Use free tier:** Most services have generous free tiers
5. **Read logs:** `make logs` helps debug issues
6. **Backup data:** Export DynamoDB tables regularly

---

## 🆘 Need Help?

1. Check **DEPLOYMENT_CHECKLIST.md** for detailed steps
2. Review **PROJECT_STATUS.md** for known issues
3. Run `make help` to see all available commands
4. Check test output: `make test -v`
5. View AWS CloudWatch logs for errors

---

## ✅ Success Checklist

After deployment, verify:
- [ ] All DynamoDB tables created
- [ ] S3 buckets created
- [ ] Lambda functions deployed
- [ ] API Gateway accessible
- [ ] Frontend loads in browser
- [ ] Can search for schemes
- [ ] Sample data loaded (8 schemes)
- [ ] Tests passing locally

---

## 🎉 You're Ready!

Your BharatSahayak system is now deployed and ready to help rural Indians access government services!

**Next Steps:**
1. Load more government schemes
2. Customize the frontend
3. Add optional features
4. Conduct user testing
5. Measure social impact

**Happy Coding! 🚀**
