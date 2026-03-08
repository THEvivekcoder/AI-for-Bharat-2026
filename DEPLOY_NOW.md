# 🚀 Deploy BharatSahayak in 4 Commands

## Prerequisites (One-Time)
1. AWS Account
2. AWS CLI installed ([Download](https://aws.amazon.com/cli/))
3. AWS SAM CLI installed ([Download](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))

---

## Deployment Commands

### 1️⃣ Configure AWS (2 minutes)
```bash
aws configure
```
Enter: Access Key, Secret Key, Region (`ap-south-1`), Format (`json`)

### 2️⃣ Install Dependencies (2 minutes)
```bash
make install
```

### 3️⃣ Create JWT Secret (1 minute)
```bash
make setup-secrets
```

### 4️⃣ Deploy Everything (10 minutes)
```bash
make deploy-all
```

**That's it!** ✨

---

## What Gets Deployed

✅ **10 DynamoDB Tables** - Users, Schemes, Profiles, Interactions, etc.  
✅ **3 S3 Buckets** - Voice data, Models, Static content  
✅ **24 Lambda Functions** - All API endpoints  
✅ **1 API Gateway** - REST API with CORS  
✅ **1 Cognito User Pool** - SMS OTP authentication  
✅ **1 OpenSearch Domain** - RAG vector database  
✅ **Sample Data** - 20+ schemes, 10 programs, 10 jobs  
✅ **Frontend** - Web interface  

---

## After Deployment

### Get Your URLs
```bash
# API URL
aws cloudformation describe-stacks --stack-name bharatsahayak \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Frontend URL
echo "http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com"
```

### Test It
```bash
# Test API
curl "YOUR_API_URL/schemes?category=agriculture"

# Open frontend in browser
# Visit the frontend URL above
```

---

## Troubleshooting

**"AWS CLI not found"**  
→ Install AWS CLI from https://aws.amazon.com/cli/

**"Unable to locate credentials"**  
→ Run `aws configure` and enter your access keys

**"Secret already exists"**  
→ This is OK! The secret was created previously

**"Stack already exists"**  
→ Run `sam deploy` to update existing stack

---

## Cost

**Development:** ~$25-50/month  
**Production (1000 users):** ~$110-180/month

Most services have free tiers for development!

---

## Need Help?

📖 **Detailed Guide:** `DEPLOYMENT_CHECKLIST.md`  
📋 **Project Status:** `PROJECT_STATUS.md`  
🎯 **Quick Start:** `QUICK_START.md`  
❓ **Commands:** `make help`

---

**Ready to deploy? Run these 4 commands! 🚀**
