# BharatSahayak Infrastructure

This directory contains infrastructure-as-code and deployment scripts for BharatSahayak.

## Directory Structure

```
infrastructure/
├── cloudformation/          # Additional CloudFormation templates
├── scripts/                 # Deployment and setup scripts
│   ├── create_dynamodb_tables.py
│   ├── setup_s3_bucket.py
│   ├── setup_cognito.py
│   └── deploy.sh
└── README.md               # This file
```

## Scripts

### 1. DynamoDB Table Creation

Creates DynamoDB tables for the application.

```bash
# Create tables in AWS
python infrastructure/scripts/create_dynamodb_tables.py dev

# Create tables in local DynamoDB
python infrastructure/scripts/create_dynamodb_tables.py dev http://localhost:8000
```

**Tables Created:**
- `bharatsahayak-users-{env}`
- `bharatsahayak-schemes-{env}`
- `bharatsahayak-user-profiles-{env}`
- `bharatsahayak-interactions-{env}`

### 2. S3 Bucket Setup

Sets up the S3 bucket folder structure for static content and scheme documents.

```bash
# Basic setup (creates folders only)
python infrastructure/scripts/setup_s3_bucket.py --environment dev

# Full setup with sample files
python infrastructure/scripts/setup_s3_bucket.py \
  --environment dev \
  --create-sample-structure

# List bucket contents
python infrastructure/scripts/setup_s3_bucket.py \
  --environment dev \
  --list-contents
```

**Folder Structure:**
- `/schemes/` - Government scheme documents (public read)
- `/documents/` - Application forms and guidelines (public read)
- `/cache/` - Cached data for offline access (private)

See [../docs/S3_SETUP.md](../docs/S3_SETUP.md) for detailed documentation.

### 3. Cognito User Pool Setup

Sets up AWS Cognito User Pool for user authentication with phone number and OTP.

```bash
# Basic setup (creates user pool only)
python infrastructure/scripts/setup_cognito.py --environment dev

# Full setup with app client
python infrastructure/scripts/setup_cognito.py \
  --environment dev \
  --create-app-client

# Display user pool information
python infrastructure/scripts/setup_cognito.py \
  --environment dev \
  --info
```

**Configuration:**
- Phone number as username (primary identifier)
- OTP-based authentication via SMS
- Custom attributes: `preferred_language`, `location`
- Token validity: 30 days (refresh), 60 minutes (access/ID)
- MFA: Optional SMS-based

See [../docs/COGNITO_SETUP.md](../docs/COGNITO_SETUP.md) for detailed documentation.

### 4. Scheme Data Loader

Loads government scheme data from JSON/CSV files or sample data into DynamoDB.

```bash
# Load sample schemes (20+ schemes across all categories)
python infrastructure/scripts/load_schemes.py --source sample

# Load from JSON file
python infrastructure/scripts/load_schemes.py \
  --source json \
  --file infrastructure/scripts/sample_schemes.json

# Load from CSV file
python infrastructure/scripts/load_schemes.py \
  --source csv \
  --file infrastructure/scripts/sample_schemes.csv

# Dry run (validate without inserting)
python infrastructure/scripts/load_schemes.py \
  --source sample \
  --dry-run

# Specify custom table and region
python infrastructure/scripts/load_schemes.py \
  --source sample \
  --table Schemes \
  --region us-east-1
```

**Features:**
- Supports JSON and CSV input formats
- Validates scheme data before insertion
- Includes 20+ sample schemes across all categories:
  - Agriculture (5 schemes)
  - Health (5 schemes)
  - Education (5 schemes)
  - Employment (5 schemes)
  - Social Welfare (5 schemes)
- Bulk insert with error handling
- Dry-run mode for validation

**Sample Data Included:**
- PM-KISAN, PMFBY, KCC (Agriculture)
- Ayushman Bharat, JSY (Health)
- NSP, MDM (Education)
- MGNREGA, PMEGP (Employment)
- NSAP, PMAY (Social Welfare)

### 5. Deployment Script

Automated deployment script for the entire stack.

```bash
# Deploy to dev environment
./infrastructure/scripts/deploy.sh dev

# Deploy to production
./infrastructure/scripts/deploy.sh prod
```

## Deployment Order

When setting up a new environment, follow this order:

1. **Deploy SAM Template**
   ```bash
   sam build
   sam deploy --guided
   ```

2. **Create DynamoDB Tables** (if not using SAM)
   ```bash
   python infrastructure/scripts/create_dynamodb_tables.py dev
   ```

3. **Setup Cognito User Pool**
   ```bash
   # First, create IAM role for Cognito SMS
   aws iam create-role \
     --role-name bharatsahayak-cognito-sms-role-dev \
     --assume-role-policy-document file://cognito-sms-trust-policy.json
   
   aws iam attach-role-policy \
     --role-name bharatsahayak-cognito-sms-role-dev \
     --policy-arn arn:aws:iam::aws:policy/service-role/AmazonCognitoSMSRole
   
   # Then create user pool
   python infrastructure/scripts/setup_cognito.py --environment dev --create-app-client
   ```

4. **Setup S3 Bucket Structure**
   ```bash
   python infrastructure/scripts/setup_s3_bucket.py --environment dev --create-sample-structure
   ```

5. **Load Scheme Data**
   ```bash
   # Load sample schemes for testing
   python infrastructure/scripts/load_schemes.py --source sample --table Schemes
   ```

6. **Verify Deployment**
   ```bash
   # Check API endpoint
   curl https://{api-id}.execute-api.ap-south-1.amazonaws.com/dev/health
   
   # Check S3 bucket
   aws s3 ls s3://bharatsahayak-static-content-dev/
   
   # Check DynamoDB tables
   aws dynamodb list-tables
   
   # Check Cognito user pool
   aws cognito-idp list-user-pools --max-results 10
   ```

## Environment Variables

The scripts use the following environment variables:

- `AWS_REGION`: AWS region (default: ap-south-1)
- `AWS_PROFILE`: AWS CLI profile to use
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

## CloudFormation Templates

The main template is `template.yaml` in the root directory. Additional templates can be placed in the `cloudformation/` directory for:

- VPC and networking
- Additional databases
- Monitoring and alerting
- CI/CD pipelines

## AWS Resources

### S3 Buckets

| Bucket | Purpose | Public Access |
|--------|---------|---------------|
| bharatsahayak-voice-data-{env} | Voice recordings | No |
| bharatsahayak-models-{env} | ML models | No |
| bharatsahayak-static-content-{env} | Scheme documents, cache | Partial (schemes/, documents/) |

### DynamoDB Tables

| Table | Primary Key | Sort Key | GSI |
|-------|-------------|----------|-----|
| users | user_id | - | phone_number |
| schemes | scheme_id | - | category |
| user-profiles | user_id | - | - |
| interactions | user_id | timestamp | - |

### IAM Roles

- Lambda execution role (managed by SAM)
- Cognito SNS role (for SMS OTP delivery)
- S3 access roles (for Lambda functions)

### Cognito User Pools

| Pool | Username | MFA | Custom Attributes |
|------|----------|-----|-------------------|
| bharatsahayak-users-{env} | phone_number | Optional SMS | preferred_language, location |

## Cost Optimization

1. **DynamoDB**: Use on-demand billing for variable workloads
2. **S3**: Lifecycle policies move old cache files to IA storage
3. **Lambda**: Right-size memory allocation based on metrics
4. **API Gateway**: Consider caching for frequently accessed endpoints

## Monitoring

Monitor infrastructure health with:

```bash
# CloudWatch logs
aws logs tail /aws/lambda/bharatsahayak-function --follow

# DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=bharatsahayak-users-dev

# S3 bucket size
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=bharatsahayak-static-content-dev
```

## Troubleshooting

### SAM Deployment Fails

```bash
# Validate template
sam validate --lint

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name bharatsahayak
```

### S3 Bucket Access Denied

```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket bharatsahayak-static-content-dev

# Check public access block
aws s3api get-public-access-block --bucket bharatsahayak-static-content-dev
```

### DynamoDB Table Not Found

```bash
# List tables
aws dynamodb list-tables

# Describe table
aws dynamodb describe-table --table-name bharatsahayak-users-dev
```

## Security Best Practices

1. **Least Privilege**: IAM roles have minimum required permissions
2. **Encryption**: All data encrypted at rest and in transit
3. **Public Access**: Only scheme/document folders are public
4. **Versioning**: Enabled on critical S3 buckets
5. **Logging**: CloudWatch logs for all Lambda functions

## Cleanup

To delete all resources:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name bharatsahayak

# Empty and delete S3 buckets (if not managed by stack)
aws s3 rm s3://bharatsahayak-static-content-dev --recursive
aws s3 rb s3://bharatsahayak-static-content-dev

# Delete DynamoDB tables (if not managed by stack)
aws dynamodb delete-table --table-name bharatsahayak-users-dev
```

## Additional Documentation

- [S3 Setup Guide](../docs/S3_SETUP.md)
- [DynamoDB Setup Guide](../docs/DYNAMODB_SETUP.md)
- [Cognito Setup Guide](../docs/COGNITO_SETUP.md)
- [AWS Setup Guide](../docs/AWS_SETUP.md)
