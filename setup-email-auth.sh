#!/bin/bash

# BharatSahayak Email Authentication Setup Script
# This script sets up the email/password authentication system

set -e

echo "🚀 BharatSahayak Email Authentication Setup"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SAM CLI found${NC}"
echo ""

# Get AWS region
read -p "Enter AWS region (default: ap-south-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-ap-south-1}

echo -e "${YELLOW}📍 Using region: $AWS_REGION${NC}"
echo ""

# Create DynamoDB tables
echo "📦 Creating DynamoDB tables..."
echo ""

# Create Users table
echo "Creating bharatsahayak-users-dev table..."
aws dynamodb create-table \
  --table-name bharatsahayak-users-dev \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION \
  2>/dev/null && echo -e "${GREEN}✅ Users table created${NC}" || echo -e "${YELLOW}⚠️  Users table already exists${NC}"

# Create Saved Schemes table
echo "Creating bharatsahayak-saved-schemes-dev table..."
aws dynamodb create-table \
  --table-name bharatsahayak-saved-schemes-dev \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=scheme_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=scheme_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION \
  2>/dev/null && echo -e "${GREEN}✅ Saved Schemes table created${NC}" || echo -e "${YELLOW}⚠️  Saved Schemes table already exists${NC}"

echo ""
echo "⏳ Waiting for tables to become active..."
sleep 5

# Update frontend files
echo ""
echo "📝 Updating frontend files..."

# Backup original files
if [ -f "frontend/api-client.js" ]; then
    cp frontend/api-client.js frontend/api-client.js.backup
    echo -e "${GREEN}✅ Backed up api-client.js${NC}"
fi

if [ -f "frontend/login.html" ]; then
    cp frontend/login.html frontend/login.html.backup
    echo -e "${GREEN}✅ Backed up login.html${NC}"
fi

# Replace with new files
cp frontend/api-client-email.js frontend/api-client.js
echo -e "${GREEN}✅ Updated api-client.js${NC}"

cp frontend/login-email.html frontend/login.html
echo -e "${GREEN}✅ Updated login.html${NC}"

# Build and deploy
echo ""
echo "🔨 Building SAM application..."
sam build

echo ""
echo "🚀 Deploying to AWS..."
echo -e "${YELLOW}Note: You may be prompted for deployment parameters${NC}"
echo ""

sam deploy --guided

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Note the API Gateway endpoint URL from the deployment output"
echo "2. Update frontend/config.json with the new API endpoint"
echo "3. Test registration at: https://your-domain/login.html"
echo "4. Check the EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md for detailed documentation"
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
