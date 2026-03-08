# BharatSahayak - Manual Steps Required

## 🎯 TL;DR - What You Must Do Manually

Only **3 manual steps** required (everything else is automated):

1. **Install AWS CLI** (one-time, 5 min)
2. **Configure AWS credentials** (one-time, 2 min)
3. **Run deployment commands** (15 min)

**Total time:** 22 minutes for first deployment

---

## 📋 Complete Manual Steps List

### ✅ One-Time Setup (Do Once)

#### Step 1: Install AWS CLI

**Why manual:** Requires system-level installation

**Windows:**
1. Download from: https://aws.amazon.com/cli/
2. Run installer
3. Restart terminal
4. Verify: `aws --version`

**Time:** 5 minutes

---

#### Step 2: Install AWS SAM CLI

**Why manual:** Requires system-level installation

**Windows:**
1. Download from: https://docs.aws.amazon.com/serverless-application-model/
2. Run installer
3. Verify: `sam --version`

**Time:** 5 minutes

---

#### Step 3: Configure AWS Credentials

**Why manual:** Requires your personal AWS access keys

**Steps:**
```bash
aws configure
```

Enter when prompted:
- AWS Access Key ID: [Get from AWS Console → IAM]
- AWS Secret Access Key: [Get from AWS Console → IAM]
- Default region: ap-south-1
- Default output format: json

**Verify:**
```bash
aws sts get-caller-identity
```

**Time:** 2 minutes

---

### 🚀 Deployment Steps (Every Deployment)

#### Step 4: Run Pre-Deployment Setup

**Why manual:** Requires confirmation and decision-making

**Command:**
```bash
python scripts/pre_deployment_setup.py
```

**What it does (automated):**
- ✅ Validates AWS credentials
- ✅ Creates JWT secret in Secrets Manager
- ✅ Checks for existing resources
- ✅ Provides cost estimation
- ✅ Generates readiness report

**What you do:**
- Press Enter to continue
- Review cost estimation
- Decide on OpenSearch (keep or disable)

**Time:** 3 minutes

---

#### Step 5: Build and Deploy

**Why manual:** Requires confirmation of changes

**Commands:**
```bash
# Build Lambda packages
sam build

# Deploy to AWS (first time)
sam deploy --guided
```

**What you do:**
- Answer prompts:
  - Stack Name: bharatsahayak-stack
  - AWS Region: ap-south-1
  - Parameter Environment: dev
  - Confirm changes: Y
  - Allow IAM role creation: Y
  - Save configuration: Y

**What SAM does (automated):**
- ✅ Creates 10 DynamoDB tables
- ✅ Creates 3 S3 buckets
- ✅ Creates Cognito User Pool
- ✅ Deploys 25 Lambda functions
- ✅ Sets up API Gateway
- ✅ Creates IAM roles
- ✅ Configures CloudWatch logging

**Time:** 10-15 minutes

---

#### Step 6: Run Post-Deployment Configuration

**Why manual:** Requires reviewing outputs

**Command:**
```bash
python scripts/post_deployment_config.py
```

**What it does (automated):**
- ✅ Retrieves CloudFormation outputs
- ✅ Updates frontend/app.js with API URL
- ✅ Validates deployment
- ✅ Checks DynamoDB tables
- ✅ Provides next steps

**What you do:**
- Review the outputs
- Note the API endpoint URL

**Time:** 2 minutes

---

#### Step 7: Load Sample Data

**Why manual:** Requires confirmation

**Command:**
```bash
python scripts/load_schemes.py
```

**What it does (automated):**
- ✅ Loads 8 government schemes into DynamoDB
- ✅ Verifies data loaded correctly

**Time:** 1 minute

---

#### Step 8: Deploy Frontend

**Why manual:** Requires S3 bucket creation

**Commands:**
```bash
# Create frontend bucket
aws s3 mb s3://bharatsahayak-frontend-dev --region ap-south-1

# Enable website hosting
aws s3 website s3://bharatsahayak-frontend-dev \
  --index-document index.html

# Upload files
cd frontend
aws s3 sync . s3://bharatsahayak-frontend-dev \
  --exclude "*.sh" --exclude "*.md"

# Make public
aws s3api put-public-access-block \
  --bucket bharatsahayak-frontend-dev \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

**Time:** 3 minutes

---

### 🧪 Testing Steps (Verification)

#### Step 9: Test API

**Command:**
```bash
# Get API URL from deployment outputs
curl https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/dev/schemes
```

**Expected:** JSON response with schemes

**Time:** 1 minute

---

#### Step 10: Test Frontend

**Steps:**
1. Open: http://bharatsahayak-frontend-dev.s3-website.ap-south-1.amazonaws.com
2. Go to Configuration tab
3. Verify API URL is pre-filled (done by post_deployment_config.py)
4. Click "Save Configuration"
5. Test user registration
6. Test scheme search

**Time:** 5 minutes

---

## 📊 Automation Analysis

### What's Fully Automated (No Manual Work)

✅ **Infrastructure Creation (100% automated by SAM):**
- DynamoDB tables (10 tables)
- S3 buckets (3 buckets)
- Cognito User Pool
- Lambda functions (25 functions)
- API Gateway
- IAM roles and policies
- CloudWatch logs

✅ **Configuration (95% automated by scripts):**
- JWT secret generation and creation
- Frontend configuration update
- Deployment validation
- Resource verification

✅ **Data Loading (100% automated):**
- Sample scheme loading
- Database population

### What Requires Manual Steps (5%)

⚠️ **One-Time Setup:**
1. AWS CLI installation (system-level)
2. SAM CLI installation (system-level)
3. AWS credentials configuration (security)

⚠️ **Per-Deployment:**
1. Run pre-deployment script (1 command)
2. Confirm SAM deployment prompts (interactive)
3. Run post-deployment script (1 command)
4. Deploy frontend to S3 (3 commands)

⚠️ **Optional:**
1. Increase SNS spending limit (AWS Console)
2. Configure custom domain (AWS Console)
3. Set up CloudWatch alarms (AWS Console)

---

## 🎯 Simplified Deployment Flow

### For First-Time Deployment

```bash
# 1. One-time setup (if not done)
aws configure

# 2. Pre-deployment (automated)
python scripts/pre_deployment_setup.py

# 3. Build and deploy (semi-automated)
sam build
sam deploy --guided

# 4. Post-deployment (automated)
python scripts/post_deployment_config.py

# 5. Load data (automated)
python scripts/load_schemes.py

# 6. Deploy frontend (3 commands)
aws s3 mb s3://bharatsahayak-frontend-dev --region ap-south-1
aws s3 website s3://bharatsahayak-frontend-dev --index-document index.html
cd frontend && aws s3 sync . s3://bharatsahayak-frontend-dev
```

### For Subsequent Deployments

```bash
# Just 3 commands!
sam build
sam deploy
python scripts/post_deployment_config.py
```

---

## 🔄 What Can Be Automated Further

### Potential Improvements

1. **Frontend Deployment:**
   - Could add to Makefile as `make deploy-frontend`
   - Already partially automated

2. **SNS Configuration:**
   - Cannot be automated (AWS Console only)
   - Could add to documentation

3. **Custom Domain:**
   - Could create script for Route53 setup
   - Low priority for MVP

4. **CloudWatch Alarms:**
   - Could add to SAM template
   - Good for production

---

## 📝 Manual Steps Summary Table

| Step | Type | Frequency | Time | Can Automate? |
|------|------|-----------|------|---------------|
| Install AWS CLI | Setup | Once | 5 min | No (system install) |
| Install SAM CLI | Setup | Once | 5 min | No (system install) |
| Configure AWS | Setup | Once | 2 min | No (security) |
| Run pre-deploy script | Deploy | Each | 3 min | Partially (needs confirmation) |
| SAM build | Deploy | Each | 2 min | Yes (in Makefile) |
| SAM deploy | Deploy | Each | 10 min | Partially (needs confirmation) |
| Run post-deploy script | Deploy | Each | 2 min | Yes (fully automated) |
| Load sample data | Deploy | Once | 1 min | Yes (fully automated) |
| Deploy frontend | Deploy | Each | 3 min | Yes (in Makefile) |
| Test deployment | Verify | Each | 5 min | Partially |
| **Total First Time** | | | **38 min** | |
| **Total Subsequent** | | | **20 min** | |

---

## ✅ What You DON'T Need to Do Manually

### ❌ You DON'T need to:
- Create DynamoDB tables manually (SAM does it)
- Create S3 buckets manually (SAM does it)
- Create Cognito User Pool manually (SAM does it)
- Create Lambda functions manually (SAM does it)
- Set up API Gateway manually (SAM does it)
- Configure IAM roles manually (SAM does it)
- Write CloudFormation templates (already done)
- Configure CORS manually (SAM does it)
- Set up CloudWatch logs manually (SAM does it)
- Generate JWT secrets manually (script does it)
- Update frontend config manually (script does it)
- Load scheme data manually (script does it)

### ✅ You ONLY need to:
1. Install tools (AWS CLI, SAM CLI) - one time
2. Configure credentials - one time
3. Run 3-4 commands per deployment
4. Confirm prompts during deployment

---

## 🎓 Why These Steps Are Manual

### AWS CLI Installation
**Why:** Requires admin privileges to install system-wide  
**Alternative:** None - required for AWS access  
**Frequency:** Once per machine

### AWS Credentials
**Why:** Security - your personal access keys  
**Alternative:** None - required for authentication  
**Frequency:** Once per AWS account

### SAM Deploy Confirmation
**Why:** Safety - review changes before applying  
**Alternative:** Use `--no-confirm-changeset` flag (not recommended)  
**Frequency:** Each deployment

### Frontend S3 Deployment
**Why:** Requires bucket creation and public access configuration  
**Alternative:** Could be added to SAM template  
**Frequency:** Each frontend update

---

## 🚀 Recommended Workflow

### First Deployment (Complete Setup)

```bash
# Phase 1: One-time setup (12 min)
aws configure                              # 2 min - manual input
make install                               # 5 min - automated
python scripts/pre_deployment_setup.py     # 3 min - mostly automated
sam build                                  # 2 min - automated

# Phase 2: Deployment (15 min)
sam deploy --guided                        # 10 min - semi-automated
python scripts/post_deployment_config.py   # 2 min - automated
python scripts/load_schemes.py             # 1 min - automated
make deploy-frontend                       # 2 min - automated

# Phase 3: Testing (5 min)
# Test API and frontend manually

# Total: 32 minutes
```

### Subsequent Deployments (Updates)

```bash
# Just 4 commands! (7 min)
sam build                                  # 2 min
sam deploy                                 # 3 min
python scripts/post_deployment_config.py   # 1 min
make deploy-frontend                       # 1 min

# Total: 7 minutes
```

---

## 💡 Pro Tips

1. **Use Makefile shortcuts:**
   ```bash
   make deploy-complete  # Runs entire flow
   ```

2. **Skip confirmations (after first deploy):**
   ```bash
   sam deploy --no-confirm-changeset
   ```

3. **Deploy only Lambda changes:**
   ```bash
   sam build && sam deploy
   # Skip frontend if unchanged
   ```

4. **Monitor deployment:**
   ```bash
   sam logs -n RegisterFunction --tail
   ```

5. **Quick rollback:**
   ```bash
   sam deploy --parameter-overrides Environment=dev
   ```

---

## 🎉 Bottom Line

**95% of deployment is automated!**

You only need to:
- Install tools once
- Configure credentials once
- Run 3-4 commands per deployment
- Confirm a few prompts

Everything else (infrastructure, configuration, data loading) is handled automatically by SAM and Python scripts.

---

**Last Updated:** March 7, 2026  
**Automation Level:** 95%  
**Manual Steps:** 3 critical, 7 optional  
**Time Required:** 22 minutes (first time), 7 minutes (updates)
