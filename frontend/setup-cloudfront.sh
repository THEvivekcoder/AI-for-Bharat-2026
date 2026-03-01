#!/bin/bash

# BharatSahayak CloudFront Setup Script
# Creates a CloudFront distribution for the frontend

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

echo -e "${GREEN}BharatSahayak CloudFront Setup${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Get S3 bucket name from CloudFormation stack
echo -e "${YELLOW}Getting S3 bucket information...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='StaticContentBucketName'].OutputValue" \
    --output text 2>/dev/null)

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}Error: Could not find S3 bucket from CloudFormation stack${NC}"
    exit 1
fi

echo -e "${GREEN}Found S3 bucket: $BUCKET_NAME${NC}"

# Get S3 website endpoint
WEBSITE_ENDPOINT="${BUCKET_NAME}.s3-website.${AWS_REGION}.amazonaws.com"

# Create CloudFront distribution configuration
echo -e "${YELLOW}Creating CloudFront distribution...${NC}"

DISTRIBUTION_CONFIG=$(cat <<EOF
{
  "CallerReference": "bharatsahayak-frontend-${ENVIRONMENT}-$(date +%s)",
  "Comment": "BharatSahayak Frontend - ${ENVIRONMENT}",
  "Enabled": true,
  "DefaultRootObject": "frontend/index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${BUCKET_NAME}",
        "DomainName": "${WEBSITE_ENDPOINT}",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${BUCKET_NAME}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 300,
    "MaxTTL": 86400,
    "Compress": true
  },
  "CacheBehaviors": {
    "Quantity": 2,
    "Items": [
      {
        "PathPattern": "frontend/*.css",
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 2,
          "Items": ["GET", "HEAD"],
          "CachedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
          }
        },
        "ForwardedValues": {
          "QueryString": false,
          "Cookies": {
            "Forward": "none"
          }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
      },
      {
        "PathPattern": "frontend/*.js",
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 2,
          "Items": ["GET", "HEAD"],
          "CachedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
          }
        },
        "ForwardedValues": {
          "QueryString": false,
          "Cookies": {
            "Forward": "none"
          }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
      }
    ]
  },
  "PriceClass": "PriceClass_100",
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true
  }
}
EOF
)

# Create the distribution
DISTRIBUTION_ID=$(echo "$DISTRIBUTION_CONFIG" | aws cloudfront create-distribution \
    --distribution-config file:///dev/stdin \
    --query 'Distribution.Id' \
    --output text 2>/dev/null)

if [ -z "$DISTRIBUTION_ID" ]; then
    echo -e "${RED}Error: Failed to create CloudFront distribution${NC}"
    exit 1
fi

echo -e "${GREEN}CloudFront distribution created: $DISTRIBUTION_ID${NC}"

# Wait for distribution to be deployed
echo -e "${YELLOW}Waiting for distribution to be deployed (this may take 10-15 minutes)...${NC}"
echo "You can continue with other tasks. Check status with:"
echo "aws cloudfront get-distribution --id $DISTRIBUTION_ID"

# Get distribution domain name
DOMAIN_NAME=$(aws cloudfront get-distribution \
    --id "$DISTRIBUTION_ID" \
    --query 'Distribution.DomainName' \
    --output text)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CloudFront Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Distribution ID: ${GREEN}${DISTRIBUTION_ID}${NC}"
echo -e "Domain Name: ${GREEN}${DOMAIN_NAME}${NC}"
echo -e "Frontend URL: ${GREEN}https://${DOMAIN_NAME}/frontend/${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Distribution deployment takes 10-15 minutes"
echo "Check status: aws cloudfront get-distribution --id $DISTRIBUTION_ID"
echo ""
echo -e "${YELLOW}To invalidate cache after updates:${NC}"
echo "aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths '/frontend/*'"
echo ""
