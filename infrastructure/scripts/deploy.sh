#!/bin/bash
# Deployment script for BharatSahayak

set -e

ENVIRONMENT=${1:-dev}

echo "Deploying BharatSahayak to $ENVIRONMENT environment..."

# Build
echo "Building SAM application..."
sam build

# Validate
echo "Validating template..."
sam validate --lint

# Deploy
echo "Deploying to AWS..."
sam deploy --parameter-overrides Environment=$ENVIRONMENT

echo "Deployment complete!"
