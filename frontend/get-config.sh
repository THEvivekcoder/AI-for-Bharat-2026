#!/bin/bash

# BharatSahayak Configuration Helper
# Retrieves API endpoint and Cognito configuration from CloudFormation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-ap-south-1}
STACK_NAME="bharatsahayak-${ENVIRONMENT}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BharatSahayak Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Stack: $STACK_NAME"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if stack exists
echo -e "${YELLOW}Checking CloudFormation stack...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].StackStatus" \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
    echo -e "${RED}Error: Stack '$STACK_NAME' not found${NC}"
    echo "Make sure the backend infrastructure is deployed first"
    exit 1
fi

if [[ "$STACK_STATUS" != *"COMPLETE"* ]]; then
    echo -e "${RED}Error: Stack is in status: $STACK_STATUS${NC}"
    echo "Wait for stack to complete deployment"
    exit 1
fi

echo -e "${GREEN}Stack found and ready${NC}"
echo ""

# Get API endpoint
echo -e "${YELLOW}Retrieving configuration...${NC}"
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text 2>/dev/null)

# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
    --output text 2>/dev/null)

# Get Client ID
CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
    --output text 2>/dev/null)

# Get S3 bucket
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='StaticContentBucketName'].OutputValue" \
    --output text 2>/dev/null)

# Get table names
USERS_TABLE=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='UsersTableName'].OutputValue" \
    --output text 2>/dev/null)

SCHEMES_TABLE=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='SchemesTableName'].OutputValue" \
    --output text 2>/dev/null)

# Display configuration
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Configuration Values${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}API Configuration:${NC}"
echo -e "API Endpoint:     ${GREEN}${API_ENDPOINT}${NC}"
echo -e "User Pool ID:     ${GREEN}${USER_POOL_ID}${NC}"
echo -e "Client ID:        ${GREEN}${CLIENT_ID}${NC}"
echo ""
echo -e "${BLUE}AWS Resources:${NC}"
echo -e "S3 Bucket:        ${GREEN}${BUCKET_NAME}${NC}"
echo -e "Users Table:      ${GREEN}${USERS_TABLE}${NC}"
echo -e "Schemes Table:    ${GREEN}${SCHEMES_TABLE}${NC}"
echo ""

# Generate website URL
WEBSITE_URL="http://${BUCKET_NAME}.s3-website.${AWS_REGION}.amazonaws.com/frontend/"

echo -e "${BLUE}Frontend URL:${NC}"
echo -e "${GREEN}${WEBSITE_URL}${NC}"
echo ""

# Create a config file
CONFIG_FILE="config.json"
cat > "$CONFIG_FILE" <<EOF
{
  "environment": "${ENVIRONMENT}",
  "region": "${AWS_REGION}",
  "apiEndpoint": "${API_ENDPOINT}",
  "userPoolId": "${USER_POOL_ID}",
  "clientId": "${CLIENT_ID}",
  "bucketName": "${BUCKET_NAME}",
  "websiteUrl": "${WEBSITE_URL}",
  "usersTable": "${USERS_TABLE}",
  "schemesTable": "${SCHEMES_TABLE}"
}
EOF

echo -e "${GREEN}Configuration saved to: ${CONFIG_FILE}${NC}"
echo ""

# Instructions
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Next Steps${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "1. Deploy the frontend:"
echo -e "   ${GREEN}./deploy.sh ${ENVIRONMENT}${NC}"
echo ""
echo "2. Open the website URL in your browser:"
echo -e "   ${GREEN}${WEBSITE_URL}${NC}"
echo ""
echo "3. In the website, configure:"
echo -e "   - API Endpoint: ${GREEN}${API_ENDPOINT}${NC}"
echo -e "   - User Pool ID: ${GREEN}${USER_POOL_ID}${NC}"
echo -e "   - Client ID:    ${GREEN}${CLIENT_ID}${NC}"
echo ""
echo "4. Test the complete user flow"
echo ""
echo -e "${YELLOW}Optional: Set up CloudFront for HTTPS${NC}"
echo -e "   ${GREEN}./setup-cloudfront.sh ${ENVIRONMENT}${NC}"
echo ""

# Check if schemes are loaded
echo -e "${YELLOW}Checking if schemes are loaded...${NC}"
SCHEME_COUNT=$(aws dynamodb scan \
    --table-name "$SCHEMES_TABLE" \
    --select "COUNT" \
    --region "$AWS_REGION" \
    --query "Count" \
    --output text 2>/dev/null || echo "0")

if [ "$SCHEME_COUNT" -eq "0" ]; then
    echo -e "${RED}Warning: No schemes found in database${NC}"
    echo "Load sample schemes with:"
    echo -e "   ${GREEN}cd ../scripts && python load_schemes.py${NC}"
else
    echo -e "${GREEN}Found ${SCHEME_COUNT} schemes in database${NC}"
fi

echo ""
