#!/bin/bash

# Deploy Modern UI to S3
BUCKET="bharatsahayak-static-content-dev"
REGION="ap-south-1"
PREFIX="modern-ui"

echo "Converting CSV to JavaScript..."
node js/convert-csv.js

echo "Deploying to S3..."
aws s3 sync . s3://$BUCKET/$PREFIX/ \
  --region $REGION \
  --exclude "*.sh" \
  --exclude "*.md" \
  --exclude "node_modules/*" \
  --exclude ".git/*" \
  --exclude "convert-csv.js"

echo "Deployment complete!"
echo "Access at: https://$BUCKET.s3.$REGION.amazonaws.com/$PREFIX/index.html"
