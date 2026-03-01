# AWS Setup Guide

This guide walks you through setting up AWS credentials and configuring your environment for BharatSahayak.

## Prerequisites

- AWS Account
- AWS CLI installed
- Python 3.11+
- AWS SAM CLI installed

## Step 1: Install AWS CLI

### Windows
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

### macOS
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## Step 2: Configure AWS Credentials

### Option 1: Using AWS CLI Configure

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your access key (from IAM console)
- **AWS Secret Access Key**: Your secret key (from IAM console)
- **Default region name**: `ap-south-1` (Mumbai, India)
- **Default output format**: `json`

### Option 2: Manual Configuration

Create/edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

Create/edit `~/.aws/config`:
```ini
[default]
region = ap-south-1
output = json
```

## Step 3: Create IAM User (if needed)

1. Go to AWS Console → IAM → Users
2. Click "Add users"
3. Enter username (e.g., `bharatsahayak-dev`)
4. Select "Programmatic access"
5. Attach policies:
   - `AWSLambdaFullAccess`
   - `AmazonAPIGatewayAdministrator`
   - `AmazonDynamoDBFullAccess`
   - `AmazonS3FullAccess`
   - `AmazonCognitoPowerUser`
   - `CloudFormationFullAccess`
   - `IAMFullAccess`
6. Save the Access Key ID and Secret Access Key

## Step 4: Verify Configuration

```bash
# Check AWS CLI version
aws --version

# Verify credentials
aws sts get-caller-identity

# List S3 buckets (to test access)
aws s3 ls
```

## Step 5: Install AWS SAM CLI

### Windows
```powershell
choco install aws-sam-cli
```

### macOS
```bash
brew install aws-sam-cli
```

### Linux
```bash
# Download the installer
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
```

### Verify SAM Installation
```bash
sam --version
```

## Step 6: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   AWS_REGION=ap-south-1
   AWS_PROFILE=default
   ENVIRONMENT=dev
   ```

## Step 7: Test Local Setup

```bash
# Build the application
sam build

# Start local API (requires Docker)
sam local start-api
```

## Region Selection

**Recommended Region**: `ap-south-1` (Mumbai, India)

**Reasons**:
- Lowest latency for Indian users
- Compliance with data residency requirements
- Full service availability

**Alternative Regions**:
- `ap-southeast-1` (Singapore) - Backup region
- `us-east-1` (N. Virginia) - For global services

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use IAM roles** for production deployments
3. **Enable MFA** on your AWS account
4. **Rotate access keys** regularly
5. **Use least privilege** principle for IAM policies
6. **Enable CloudTrail** for audit logging

## Troubleshooting

### "Unable to locate credentials"
- Verify `~/.aws/credentials` exists and is properly formatted
- Check AWS_PROFILE environment variable
- Run `aws configure` to reconfigure

### "Access Denied" errors
- Verify IAM user has necessary permissions
- Check policy attachments in IAM console
- Ensure region is correct

### SAM build fails
- Verify Python 3.11 is installed
- Check Docker is running (for local testing)
- Ensure all dependencies in requirements.txt are valid

## Next Steps

After AWS setup is complete:
1. Review the main README.md for project setup
2. Run `make install` to install dependencies
3. Run `make build` to build the SAM application
4. Run `make deploy` to deploy to AWS

## Support

For AWS-specific issues:
- AWS Documentation: https://docs.aws.amazon.com/
- AWS SAM Documentation: https://docs.aws.amazon.com/serverless-application-model/
- AWS Support: https://console.aws.amazon.com/support/
