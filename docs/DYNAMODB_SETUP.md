# DynamoDB Setup Guide

This guide explains how to set up DynamoDB tables for BharatSahayak.

## Table Overview

BharatSahayak uses four core DynamoDB tables:

### 1. Users Table
- **Purpose**: Store user authentication and basic information
- **Partition Key**: `user_id` (String)
- **Global Secondary Index**: `phone-number-index` on `phone_number`
- **Billing Mode**: Pay per request
- **Attributes**:
  - `user_id`: Unique user identifier (UUID)
  - `phone_number`: User's phone number (unique)
  - `language`: Preferred language
  - `created_at`: Account creation timestamp
  - `updated_at`: Last update timestamp

### 2. Schemes Table
- **Purpose**: Store government scheme information
- **Partition Key**: `scheme_id` (String)
- **Global Secondary Index**: `category-index` on `category`
- **Billing Mode**: Pay per request
- **Attributes**:
  - `scheme_id`: Unique scheme identifier (UUID)
  - `category`: Scheme category (agriculture, health, education, etc.)
  - `name`: Scheme name
  - `description`: Detailed description
  - `eligibility_criteria`: JSON object with criteria
  - `benefits`: List of benefits
  - `application_process`: Step-by-step application guide
  - `last_updated`: Last verification timestamp

### 3. UserProfiles Table
- **Purpose**: Store detailed user profile information
- **Partition Key**: `user_id` (String)
- **Billing Mode**: Pay per request
- **Attributes**:
  - `user_id`: Reference to Users table
  - `location`: JSON object (state, district, pincode)
  - `age`: User age
  - `gender`: User gender
  - `education_level`: Education qualification
  - `occupation`: Current occupation
  - `income_bracket`: Income range
  - `household_size`: Number of family members
  - `preferences`: JSON object with user preferences

### 4. Interactions Table
- **Purpose**: Track user interactions for analytics and impact measurement
- **Partition Key**: `user_id` (String)
- **Sort Key**: `timestamp` (Number - Unix timestamp)
- **Billing Mode**: Pay per request
- **Attributes**:
  - `user_id`: Reference to Users table
  - `timestamp`: Unix timestamp of interaction
  - `event_type`: Type of interaction (query_submitted, scheme_accessed, etc.)
  - `event_data`: JSON object with event details
  - `language`: Language used for interaction
  - `session_id`: Session identifier

## Setup Methods

### Method 1: AWS SAM Deployment (Recommended for Production)

The tables are defined in `template.yaml` and will be automatically created when you deploy using SAM:

```bash
# Build the application
sam build

# Deploy (creates all resources including DynamoDB tables)
sam deploy --guided
```

During guided deployment, you'll be prompted for:
- Stack name
- AWS Region (recommend: ap-south-1)
- Environment (dev/staging/prod)

### Method 2: Python Script (For Development/Testing)

Use the provided Python script to create tables manually:

```bash
# For AWS deployment
python infrastructure/scripts/create_dynamodb_tables.py dev

# For staging environment
python infrastructure/scripts/create_dynamodb_tables.py staging

# For production environment
python infrastructure/scripts/create_dynamodb_tables.py prod
```

### Method 3: Local DynamoDB (For Local Development)

1. **Install and run DynamoDB Local**:
   ```bash
   # Using Docker
   docker run -p 8000:8000 amazon/dynamodb-local
   
   # Or download from AWS
   # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
   ```

2. **Create tables pointing to local endpoint**:
   ```bash
   python infrastructure/scripts/create_dynamodb_tables.py dev http://localhost:8000
   ```

3. **Configure your application to use local DynamoDB**:
   ```python
   # In your code
   import boto3
   
   dynamodb = boto3.resource(
       'dynamodb',
       endpoint_url='http://localhost:8000',
       region_name='ap-south-1'
   )
   ```

## Verification

### Check Tables in AWS Console

1. Go to AWS Console → DynamoDB → Tables
2. Verify all four tables exist:
   - `bharatsahayak-users-{environment}`
   - `bharatsahayak-schemes-{environment}`
   - `bharatsahayak-user-profiles-{environment}`
   - `bharatsahayak-interactions-{environment}`

### Check Tables Using AWS CLI

```bash
# List all tables
aws dynamodb list-tables --region ap-south-1

# Describe a specific table
aws dynamodb describe-table \
  --table-name bharatsahayak-users-dev \
  --region ap-south-1

# Check table status
aws dynamodb describe-table \
  --table-name bharatsahayak-users-dev \
  --query 'Table.TableStatus' \
  --region ap-south-1
```

### Check Tables Using Python

```python
import boto3

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# List tables
tables = list(dynamodb.tables.all())
for table in tables:
    print(f"Table: {table.name}, Status: {table.table_status}")

# Get table details
table = dynamodb.Table('bharatsahayak-users-dev')
print(f"Item count: {table.item_count}")
print(f"Key schema: {table.key_schema}")
```

## Data Access Patterns

### Users Table
- **Get user by ID**: Direct key lookup on `user_id`
- **Find user by phone**: Query using `phone-number-index` GSI

### Schemes Table
- **Get scheme by ID**: Direct key lookup on `scheme_id`
- **List schemes by category**: Query using `category-index` GSI
- **Search schemes**: Scan with filter (consider adding search index for production)

### UserProfiles Table
- **Get profile**: Direct key lookup on `user_id`
- **Update profile**: Update item by `user_id`

### Interactions Table
- **Get user interactions**: Query by `user_id`
- **Get recent interactions**: Query by `user_id` with sort key condition on `timestamp`
- **Get interactions in time range**: Query with `timestamp` between conditions

## Cost Optimization

All tables use **Pay Per Request** billing mode, which is ideal for:
- Unpredictable workloads
- Development and testing
- Applications with sporadic traffic

For production with consistent traffic, consider switching to **Provisioned Capacity** with auto-scaling.

## Backup and Recovery

### Enable Point-in-Time Recovery (PITR)

```bash
aws dynamodb update-continuous-backups \
  --table-name bharatsahayak-users-prod \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --region ap-south-1
```

### Create On-Demand Backup

```bash
aws dynamodb create-backup \
  --table-name bharatsahayak-users-prod \
  --backup-name users-backup-$(date +%Y%m%d) \
  --region ap-south-1
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics in CloudWatch:
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `UserErrors`
- `SystemErrors`
- `ThrottledRequests`

### Set Up Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name bharatsahayak-users-throttled \
  --alarm-description "Alert when DynamoDB requests are throttled" \
  --metric-name ThrottledRequests \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=TableName,Value=bharatsahayak-users-prod \
  --evaluation-periods 1
```

## Troubleshooting

### Table Already Exists Error
If you see "ResourceInUseException", the table already exists. Either:
- Use the existing table
- Delete the table first: `aws dynamodb delete-table --table-name <table-name>`
- Use a different environment name

### Access Denied Error
Ensure your IAM user/role has these permissions:
- `dynamodb:CreateTable`
- `dynamodb:DescribeTable`
- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:Query`
- `dynamodb:Scan`

### Connection Timeout (Local DynamoDB)
- Verify DynamoDB Local is running: `docker ps`
- Check the endpoint URL is correct: `http://localhost:8000`
- Ensure no firewall is blocking port 8000

## Next Steps

After setting up DynamoDB tables:
1. Implement repository classes in `src/services/`
2. Create data models in `src/models/`
3. Write unit tests for database operations
4. Load sample scheme data for testing

## References

- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [DynamoDB Local Setup](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
