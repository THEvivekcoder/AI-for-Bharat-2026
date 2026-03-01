#!/bin/bash

# BharatSahayak Frontend Deployment Script
# Deploys static files to S3 and optionally creates CloudFront distribution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-ap-south-1}
STACK_NAME="bharatsahayak-${ENVIRONMENT}"

echo -e "${GREEN}BharatSahayak Frontend Deployment${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Get S3 bucket name from CloudFormation stack
echo -e "${YELLOW}Getting S3 bucket name from CloudFormation...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='StaticContentBucketName'].OutputValue" \
    --output text 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}Error: Could not find S3 bucket from CloudFormation stack${NC}"
    echo "Make sure the backend stack is deployed first"
    exit 1
fi

echo -e "${GREEN}Found S3 bucket: $BUCKET_NAME${NC}"

# Create a frontend folder in the bucket
FRONTEND_PREFIX="frontend"

# Upload files to S3
echo -e "${YELLOW}Uploading files to S3...${NC}"

# Upload HTML
aws s3 cp index.html "s3://${BUCKET_NAME}/${FRONTEND_PREFIX}/index.html" \
    --content-type "text/html" \
    --cache-control "max-age=300" \
    --region "$AWS_REGION"

# Upload CSS
aws s3 cp styles.css "s3://${BUCKET_NAME}/${FRONTEND_PREFIX}/styles.css" \
    --content-type "text/css" \
    --cache-control "max-age=86400" \
    --region "$AWS_REGION"

# Upload JavaScript
aws s3 cp app.js "s3://${BUCKET_NAME}/${FRONTEND_PREFIX}/app.js" \
    --content-type "application/javascript" \
    --cache-control "max-age=86400" \
    --region "$AWS_REGION"

# Upload README
aws s3 cp README.md "s3://${BUCKET_NAME}/${FRONTEND_PREFIX}/README.md" \
    --content-type "text/markdown" \
    --cache-control "max-age=3600" \
    --region "$AWS_REGION"

echo -e "${GREEN}Files uploaded successfully!${NC}"

# Set bucket policy for public read access to frontend folder
echo -e "${YELLOW}Updating bucket policy for public access...${NC}"

BUCKET_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}/schemes/*",
        "arn:aws:s3:::${BUCKET_NAME}/documents/*",
        "arn:aws:s3:::${BUCKET_NAME}/${FRONTEND_PREFIX}/*"
      ]
    },
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "schemes/*",
            "documents/*",
            "${FRONTEND_PREFIX}/*"
          ]
        }
      }
    }
  ]
}
EOF
)

echo "$BUCKET_POLICY" | aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy file:///dev/stdin \
    --region "$AWS_REGION"

echo -e "${GREEN}Bucket policy updated!${NC}"

# Enable static website hosting
echo -e "${YELLOW}Configuring static website hosting...${NC}"

aws s3 website "s3://${BUCKET_NAME}" \
    --index-document "${FRONTEND_PREFIX}/index.html" \
    --error-document "${FRONTEND_PREFIX}/index.html" \
    --region "$AWS_REGION"

echo -e "${GREEN}Static website hosting enabled!${NC}"

# Get website URL
WEBSITE_URL="http://${BUCKET_NAME}.s3-website.${AWS_REGION}.amazonaws.com/${FRONTEND_PREFIX}/"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "S3 Bucket: ${GREEN}${BUCKET_NAME}${NC}"
echo -e "Website URL: ${GREEN}${WEBSITE_URL}${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open the website URL in your browser"
echo "2. Configure API endpoint and Cognito credentials"
echo "3. Test the complete user flow"
echo ""
echo -e "${YELLOW}Optional: Set up CloudFront for HTTPS${NC}"
echo "Run: ./setup-cloudfront.sh $ENVIRONMENT"
echo ""
