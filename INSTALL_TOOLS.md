# BharatSahayak - Tool Installation Guide

## 🚨 DEPLOYMENT BLOCKED - Required Tools Not Installed

Your system is missing the required deployment tools. You need to install these before deployment can proceed.

---

## ✅ What You Need to Install

### 1. AWS CLI (Required)
**Status:** ❌ Not installed  
**Purpose:** Interact with AWS services  
**Time:** 5 minutes

### 2. AWS SAM CLI (Required)
**Status:** ❌ Not installed  
**Purpose:** Deploy serverless applications  
**Time:** 5 minutes

### 3. Python 3.11 (Already Installed)
**Status:** ✅ Installed  
**Purpose:** Run Lambda functions and scripts

---

## 📥 Installation Instructions

### Step 1: Install AWS CLI

#### Option A: MSI Installer (Recommended for Windows)

1. **Download the installer:**
   - Visit: https://aws.amazon.com/cli/
   - Click "Download for Windows"
   - Or direct link: https://awscli.amazonaws.com/AWSCLIV2.msi

2. **Run the installer:**
   - Double-click the downloaded .msi file
   - Follow the installation wizard
   - Accept default settings

3. **Restart your terminal:**
   - Close all PowerShell/Command Prompt windows
   - Open a new terminal

4. **Verify installation:**
   ```bash
   aws --version
   ```
   Expected output: `aws-cli/2.x.x Python/3.x.x Windows/...`

#### Option B: Using Python pip

```bash
pip install awscli
```

**Verify:**
```bash
aws --version
```

---

### Step 2: Install AWS SAM CLI

#### Option A: MSI Installer (Recommended for Windows)

1. **Download the installer:**
   - Visit: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
   - Scroll to "Windows" section
   - Click download link for SAM CLI MSI
   - Or direct link: https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi

2. **Run the installer:**
   - Double-click the downloaded .msi file
   - Follow the installation wizard
   - Accept default settings

3. **Restart your terminal:**
   - Close all PowerShell/Command Prompt windows
   - Open a new terminal

4. **Verify installation:**
   ```bash
   sam --version
   ```
   Expected output: `SAM CLI, version 1.x.x`

#### Option B: Using Chocolatey (if you have it)

```bash
choco install aws-sam-cli
```

#### Option C: Using pip (alternative)

```bash
pip install aws-sam-cli
```

**Verify:**
```bash
sam --version
```

---

### Step 3: Configure AWS Credentials

After installing AWS CLI, you need to configure your credentials:

```bash
aws configure
```

**You'll be prompted for:**

1. **AWS Access Key ID:**
   - Get from AWS Console → IAM → Users → Your User → Security Credentials
   - Click "Create access key"
   - Copy the Access Key ID

2. **AWS Secret Access Key:**
   - Shown only once when creating access key
   - Copy and save securely

3. **Default region name:**
   - Enter: `ap-south-1` (Mumbai region)

4. **Default output format:**
   - Enter: `json`

**Verify configuration:**
```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## 🔍 Troubleshooting Installation

### Issue: "aws not recognized" after installation

**Solution:**
1. Restart your terminal completely
2. Check if AWS CLI is in PATH:
   ```bash
   where aws
   ```
3. If not found, add to PATH manually:
   - Search "Environment Variables" in Windows
   - Edit PATH variable
   - Add: `C:\Program Files\Amazon\AWSCLIV2`

### Issue: "sam not recognized" after installation

**Solution:**
1. Restart your terminal completely
2. Check if SAM CLI is in PATH:
   ```bash
   where sam
   ```
3. If not found, add to PATH manually:
   - Add: `C:\Program Files\Amazon\AWSSAMCLI\bin`

### Issue: "Access Denied" when running aws commands

**Solution:**
1. Verify credentials are configured:
   ```bash
   aws configure list
   ```
2. Check IAM user has required permissions:
   - CloudFormation
   - Lambda
   - DynamoDB
   - S3
   - Cognito
   - IAM (for role creation)

---

## ✅ Installation Verification Checklist

Run these commands to verify everything is installed:

```bash
# Check AWS CLI
aws --version
# Expected: aws-cli/2.x.x

# Check SAM CLI
sam --version
# Expected: SAM CLI, version 1.x.x

# Check Python
python --version
# Expected: Python 3.11.x

# Check AWS credentials
aws sts get-caller-identity
# Expected: JSON with your account details

# Check pip packages
pip list | grep -E "boto3|pytest|hypothesis"
# Expected: boto3, pytest, hypothesis listed
```

If all commands work, you're ready to deploy! ✅

---

## 🚀 After Installation - Next Steps

Once tools are installed:

```bash
# 1. Run pre-deployment setup
python scripts/pre_deployment_setup.py

# 2. Build application
sam build

# 3. Deploy to AWS
sam deploy --guided

# 4. Post-deployment configuration
python scripts/post_deployment_config.py

# 5. Load sample data
python scripts/load_schemes.py

# 6. Deploy frontend
make deploy-frontend
```

---

## 📚 Additional Resources

### AWS CLI Documentation
- Installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Configuration: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html
- User Guide: https://docs.aws.amazon.com/cli/latest/userguide/

### SAM CLI Documentation
- Installation: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
- Getting Started: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started.html
- User Guide: https://docs.aws.amazon.com/serverless-application-model/

### AWS Account Setup
- Create Account: https://aws.amazon.com/free/
- IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- Free Tier: https://aws.amazon.com/free/

---

## 💡 Pro Tips

1. **Use AWS Free Tier:**
   - Most services have generous free tiers
   - Perfect for student projects
   - Monitor usage to avoid charges

2. **Create IAM User (Don't use root):**
   - Create dedicated IAM user for deployment
   - Attach policies: AdministratorAccess (for testing)
   - Use MFA for security

3. **Save Your Access Keys:**
   - Store securely (password manager)
   - Never commit to git
   - Rotate regularly

4. **Test in Mumbai Region:**
   - Use ap-south-1 (Mumbai)
   - Lowest latency for India
   - All services available

---

## ⏱️ Time Estimate

- AWS CLI installation: 5 minutes
- SAM CLI installation: 5 minutes
- AWS credentials setup: 5 minutes
- Verification: 2 minutes

**Total: 17 minutes**

After this, deployment takes 30 minutes.

---

## 🆘 Need Help?

If you encounter issues during installation:

1. **Check Windows version:**
   - AWS CLI requires Windows 10 or later
   - SAM CLI requires Windows 10 or later

2. **Run as Administrator:**
   - Right-click installer
   - Select "Run as administrator"

3. **Check antivirus:**
   - Some antivirus software blocks installers
   - Temporarily disable if needed

4. **Use alternative installation:**
   - Try pip install method
   - Or use Chocolatey package manager

---

## 📞 Support

**AWS Support:**
- Documentation: https://docs.aws.amazon.com/
- Forums: https://forums.aws.amazon.com/
- Support: https://console.aws.amazon.com/support/

**Project Support:**
- Check DEPLOYMENT_CHECKLIST.md
- Review BUGS_AND_FIXES.md
- Run: `make help`

---

**NEXT STEP:** Install AWS CLI and SAM CLI, then run deployment commands!

**Last Updated:** March 7, 2026
