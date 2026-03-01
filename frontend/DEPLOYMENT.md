# Frontend Deployment Guide

This guide explains how to deploy the BharatSahayak frontend to AWS S3 and optionally set up CloudFront for HTTPS access.

## Prerequisites

1. AWS CLI installed and configured
2. Backend infrastructure deployed (CloudFormation stack)
3. Appropriate AWS permissions for S3 and CloudFront

## Deployment Steps

### Step 1: Deploy to S3

The simplest deployment option is to upload the static files to the existing S3 bucket created by the backend CloudFormation stack.

```bash
cd frontend
chmod +x deploy.sh
./deploy.sh dev
```

This script will:
1. Get the S3 bucket name from CloudFormation outputs
2. Upload all frontend files to the `frontend/` prefix in the bucket
3. Update bucket policy to allow public read access
4. Enable static website hosting
5. Display the website URL

**Output:**
```
S3 Bucket: bharatsahayak-static-content-dev
Website URL: http://bharatsahayak-static-content-dev.s3-website.ap-south-1.amazonaws.com/frontend/
```

### Step 2: Configure the Frontend

1. Open the website URL in your browser
2. In the "API Configuration" section, enter:
   - **API Endpoint**: Your API Gateway URL (from CloudFormation outputs)
   - **User Pool ID**: Your Cognito User Pool ID (from CloudFormation outputs)
   - **Client ID**: Your Cognito Client ID (from CloudFormation outputs)
3. Click "Save Configuration"

**Getting Configuration Values:**

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text

# Get User Pool ID
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text

# Get Client ID
aws cloudformation describe-stacks \
  --stack-name bharatsahayak-dev \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
  --output text
```

### Step 3: Test the Frontend

1. **Register a new user**:
   - Enter phone number (format: +919876543210)
   - Select language
   - Click "Register"
   - Check CloudWatch logs for OTP (in dev environment)

2. **Login**:
   - Enter phone number and OTP
   - Click "Verify & Login"

3. **Update profile**:
   - Fill in demographic information
   - Click "Update Profile"

4. **Search schemes**:
   - Enter keywords or browse all
   - View scheme details
   - Check eligibility

### Step 4 (Optional): Set Up CloudFront

For HTTPS access and better performance, set up a CloudFront distribution:

```bash
cd frontend
chmod +x setup-cloudfront.sh
./setup-cloudfront.sh dev
```

This script will:
1. Create a CloudFront distribution pointing to your S3 bucket
2. Configure caching rules for optimal performance
3. Enable HTTPS with CloudFront default certificate
4. Display the CloudFront URL

**Note:** CloudFront distribution deployment takes 10-15 minutes.

**Output:**
```
Distribution ID: E1234567890ABC
Domain Name: d1234567890abc.cloudfront.net
Frontend URL: https://d1234567890abc.cloudfront.net/frontend/
```

## Manual Deployment (Alternative)

If you prefer to deploy manually:

### Upload to S3

```bash
# Set variables
BUCKET_NAME="bharatsahayak-static-content-dev"
AWS_REGION="ap-south-1"

# Upload files
aws s3 cp index.html s3://${BUCKET_NAME}/frontend/index.html \
  --content-type "text/html" \
  --region ${AWS_REGION}

aws s3 cp styles.css s3://${BUCKET_NAME}/frontend/styles.css \
  --content-type "text/css" \
  --region ${AWS_REGION}

aws s3 cp app.js s3://${BUCKET_NAME}/frontend/app.js \
  --content-type "application/javascript" \
  --region ${AWS_REGION}
```

### Update Bucket Policy

```bash
# Create policy file
cat > bucket-policy.json <<EOF
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
        "arn:aws:s3:::${BUCKET_NAME}/frontend/*"
      ]
    }
  ]
}
EOF

# Apply policy
aws s3api put-bucket-policy \
  --bucket ${BUCKET_NAME} \
  --policy file://bucket-policy.json \
  --region ${AWS_REGION}
```

### Enable Static Website Hosting

```bash
aws s3 website s3://${BUCKET_NAME} \
  --index-document frontend/index.html \
  --error-document frontend/index.html \
  --region ${AWS_REGION}
```

## Updating the Frontend

After making changes to the frontend files:

### Update S3

```bash
cd frontend
./deploy.sh dev
```

### Invalidate CloudFront Cache (if using CloudFront)

```bash
DISTRIBUTION_ID="E1234567890ABC"  # Your distribution ID

aws cloudfront create-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --paths "/frontend/*"
```

## Troubleshooting

### Issue: "Access Denied" when accessing website

**Solution:**
- Check bucket policy allows public read access
- Verify bucket is not blocking public access
- Check S3 bucket public access settings

```bash
# Check public access block
aws s3api get-public-access-block --bucket ${BUCKET_NAME}

# If needed, remove public access block
aws s3api delete-public-access-block --bucket ${BUCKET_NAME}
```

### Issue: "Failed to fetch" errors in browser

**Solution:**
- Verify API Gateway CORS is configured correctly
- Check API endpoint URL is correct
- Ensure API Gateway is deployed to the correct stage

### Issue: CloudFront shows old content

**Solution:**
- Create a cache invalidation
- Wait a few minutes for invalidation to complete

```bash
aws cloudfront create-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --paths "/frontend/*"
```

### Issue: OTP not received

**Solution:**
- In dev environment, OTPs are logged to CloudWatch
- Check Lambda function logs for the registration function
- Verify Cognito SMS configuration

```bash
# View recent logs
aws logs tail /aws/lambda/bharatsahayak-register-dev --follow
```

## Security Considerations

### Production Deployment

For production deployment, consider:

1. **Custom Domain**: Use Route 53 and ACM for custom domain with SSL
2. **WAF**: Add AWS WAF to CloudFront for DDoS protection
3. **Authentication**: Consider adding CloudFront signed URLs for sensitive content
4. **Monitoring**: Set up CloudWatch alarms for 4xx/5xx errors
5. **Backup**: Enable S3 versioning for rollback capability

### CORS Configuration

Ensure API Gateway CORS is properly configured:

```yaml
Cors:
  AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
  AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With'"
  AllowOrigin: "'*'"  # In production, specify your CloudFront domain
  MaxAge: "'600'"
```

## Cost Optimization

### S3 Costs
- Frontend files are small (~50KB total)
- Minimal storage costs
- Pay per request (GET requests)

### CloudFront Costs
- Free tier: 1TB data transfer out per month
- Pay per request after free tier
- Consider PriceClass_100 for cost optimization (US, Canada, Europe)

### Estimated Monthly Costs (1000 users)
- S3: ~$0.10
- CloudFront: ~$1-2 (within free tier for small projects)
- Total: ~$1-2/month

## Next Steps

After successful deployment:

1. Test all features end-to-end
2. Load sample scheme data into DynamoDB
3. Test with real users
4. Monitor CloudWatch logs for errors
5. Set up CloudWatch alarms for monitoring
6. Consider adding Google Analytics or similar for usage tracking

## Additional Resources

- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)
