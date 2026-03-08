#!/bin/bash

# BharatSahayak Frontend Deployment Script

set -e

# Default environment
ENVIRONMENT=${1:-dev}

echo "🚀 Deploying BharatSahayak Frontend to $ENVIRONMENT environment..."

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ Error: Environment must be dev, staging, or prod"
    exit 1
fi

# Copy appropriate config file
echo "📋 Setting up configuration for $ENVIRONMENT..."
if [ -f "config.$ENVIRONMENT.json" ]; then
    cp "config.$ENVIRONMENT.json" "config.json"
    echo "✅ Configuration set for $ENVIRONMENT"
else
    echo "⚠️  Warning: config.$ENVIRONMENT.json not found, using default config.json"
fi

# Minify CSS and JavaScript for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🗜️  Minifying assets for production..."
    
    # Install dependencies if needed
    if ! command -v cssnano &> /dev/null; then
        echo "Installing cssnano..."
        npm install -g cssnano-cli
    fi
    
    if ! command -v terser &> /dev/null; then
        echo "Installing terser..."
        npm install -g terser
    fi
    
    # Minify CSS
    if [ -f "styles.css" ]; then
        cssnano styles.css styles.min.css
        echo "✅ CSS minified"
    fi
    
    # Minify JavaScript
    if [ -f "app.js" ]; then
        terser app.js -o app.min.js --compress --mangle
        echo "✅ JavaScript minified"
    fi
    
    # Update HTML files to use minified assets
    for file in *.html; do
        if [ -f "$file" ]; then
            sed -i 's/styles\.css/styles.min.css/g' "$file"
            sed -i 's/app\.js/app.min.js/g' "$file"
        fi
    done
    
    echo "✅ HTML files updated to use minified assets"
fi

# Validate HTML files
echo "🔍 Validating HTML files..."
for file in *.html; do
    if [ -f "$file" ]; then
        # Basic validation - check for required elements
        if ! grep -q "<!DOCTYPE html>" "$file"; then
            echo "⚠️  Warning: $file missing DOCTYPE declaration"
        fi
        if ! grep -q "<title>" "$file"; then
            echo "⚠️  Warning: $file missing title tag"
        fi
        echo "✅ $file validated"
    fi
done

# Create manifest for PWA
echo "📱 Updating PWA manifest..."
if [ -f "manifest.json" ]; then
    # Update start_url based on environment
    if [ "$ENVIRONMENT" = "prod" ]; then
        sed -i 's/"start_url": ".*"/"start_url": "\/"/g' manifest.json
    else
        sed -i 's/"start_url": ".*"/"start_url": "\/"/g' manifest.json
    fi
    echo "✅ PWA manifest updated"
fi

# Generate service worker cache version
CACHE_VERSION=$(date +%s)
if [ -f "service-worker.js" ]; then
    sed -i "s/CACHE_VERSION = '[^']*'/CACHE_VERSION = 'v$CACHE_VERSION'/g" service-worker.js
    echo "✅ Service worker cache version updated to v$CACHE_VERSION"
fi

# Deploy to S3 (if AWS CLI is configured)
if command -v aws &> /dev/null; then
    echo "☁️  Checking AWS configuration..."
    
    # Set S3 bucket based on environment
    case $ENVIRONMENT in
        dev)
            S3_BUCKET="bharatsahayak-frontend-dev"
            ;;
        staging)
            S3_BUCKET="bharatsahayak-frontend-staging"
            ;;
        prod)
            S3_BUCKET="bharatsahayak-frontend-prod"
            ;;
    esac
    
    echo "📤 Deploying to S3 bucket: $S3_BUCKET"
    
    # Sync files to S3
    aws s3 sync . s3://$S3_BUCKET/ \
        --exclude "*.sh" \
        --exclude "*.md" \
        --exclude ".git/*" \
        --exclude "node_modules/*" \
        --exclude "config.*.json" \
        --cache-control "public, max-age=31536000" \
        --metadata-directive REPLACE
    
    # Set special cache headers for HTML files
    aws s3 cp . s3://$S3_BUCKET/ \
        --recursive \
        --exclude "*" \
        --include "*.html" \
        --cache-control "public, max-age=300" \
        --metadata-directive REPLACE
    
    # Set cache headers for config.json
    aws s3 cp config.json s3://$S3_BUCKET/config.json \
        --cache-control "public, max-age=300" \
        --metadata-directive REPLACE
    
    echo "✅ Files deployed to S3"
    
    # Invalidate CloudFront cache if distribution exists
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[0].DomainName=='$S3_BUCKET.s3.amazonaws.com'].Id" --output text)
    
    if [ ! -z "$CLOUDFRONT_DISTRIBUTION_ID" ] && [ "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]; then
        echo "🔄 Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
            --paths "/*"
        echo "✅ CloudFront cache invalidated"
    fi
    
else
    echo "⚠️  AWS CLI not found. Skipping S3 deployment."
    echo "📁 Files are ready for manual deployment in current directory"
fi

# Generate deployment report
echo "📊 Generating deployment report..."
cat > deployment-report.txt << EOF
BharatSahayak Frontend Deployment Report
========================================

Environment: $ENVIRONMENT
Deployment Date: $(date)
Cache Version: v$CACHE_VERSION

Files Deployed:
$(ls -la *.html *.css *.js *.json 2>/dev/null || echo "No files found")

Configuration:
$(cat config.json 2>/dev/null || echo "No config.json found")

Status: ✅ DEPLOYED SUCCESSFULLY
EOF

echo "✅ Deployment report generated: deployment-report.txt"

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Test the application in $ENVIRONMENT environment"
echo "2. Verify API endpoints are working"
echo "3. Check PWA installation on mobile devices"
echo "4. Monitor CloudWatch logs for any errors"
echo ""
echo "🌐 Application URLs:"
case $ENVIRONMENT in
    dev)
        echo "   Development: https://dev.bharatsahayak.gov.in"
        ;;
    staging)
        echo "   Staging: https://staging.bharatsahayak.gov.in"
        ;;
    prod)
        echo "   Production: https://bharatsahayak.gov.in"
        ;;
esac
echo ""