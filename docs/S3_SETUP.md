# S3 Bucket Setup for BharatSahayak

This document describes the S3 bucket configuration for storing static content, scheme documents, and cached data for offline functionality.

## Overview

The `bharatsahayak-static-content-{environment}` bucket stores:

1. **Scheme Documents** (`/schemes`): Government scheme information and PDFs
2. **General Documents** (`/documents`): Application forms, guidelines, and resources
3. **Cached Data** (`/cache`): Cached content for offline and low-bandwidth access

## Bucket Configuration

### Features

- **Versioning**: Enabled to track document changes
- **Public Read Access**: Scheme and document folders are publicly readable
- **CORS**: Configured for web application access
- **Lifecycle Policies**:
  - Cache files older than 30 days → moved to Infrequent Access storage
  - Cache files older than 90 days → automatically deleted

### Folder Structure

```
bharatsahayak-static-content-{env}/
├── schemes/
│   ├── central/          # Central government schemes
│   └── state/            # State-specific schemes
├── documents/
│   ├── application-forms/  # Downloadable forms
│   └── guidelines/         # Instructions and guides
└── cache/
    ├── schemes/          # Cached scheme data (JSON)
    ├── prices/           # Cached mandi prices (JSON)
    └── weather/          # Cached weather data (JSON)
```

## Deployment

### 1. Deploy CloudFormation Stack

The S3 bucket is defined in `template.yaml` and deployed via AWS SAM:

```bash
# Build and deploy the stack
sam build
sam deploy --guided

# Or use the Makefile
make deploy
```

### 2. Setup Folder Structure

After deploying the stack, run the setup script to create the folder structure:

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

### 3. Verify Setup

Check that the bucket is properly configured:

```bash
# Get bucket info
aws s3api head-bucket --bucket bharatsahayak-static-content-dev

# List bucket contents
aws s3 ls s3://bharatsahayak-static-content-dev/ --recursive

# Test public access to a scheme document
curl https://bharatsahayak-static-content-dev.s3.ap-south-1.amazonaws.com/schemes/central/pm-kisan-sample.json
```

## Bucket Policy

The bucket policy allows:

1. **Public Read Access** to `/schemes/*` and `/documents/*`
2. **List Access** to browse scheme and document folders
3. **Private Access** to `/cache/*` (requires authentication)

Example policy statement:

```json
{
  "Sid": "PublicReadGetObject",
  "Effect": "Allow",
  "Principal": "*",
  "Action": ["s3:GetObject"],
  "Resource": [
    "arn:aws:s3:::bharatsahayak-static-content-dev/schemes/*",
    "arn:aws:s3:::bharatsahayak-static-content-dev/documents/*"
  ]
}
```

## Usage

### Uploading Scheme Documents

```bash
# Upload a scheme document
aws s3 cp scheme.json \
  s3://bharatsahayak-static-content-dev/schemes/central/scheme-name.json \
  --content-type application/json \
  --metadata scheme-id=scheme-001,category=agriculture

# Upload a PDF document
aws s3 cp scheme.pdf \
  s3://bharatsahayak-static-content-dev/documents/application-forms/scheme-form.pdf \
  --content-type application/pdf
```

### Accessing Documents

Public URLs follow this pattern:

```
https://bharatsahayak-static-content-{env}.s3.{region}.amazonaws.com/{path}
```

Examples:

```
# Scheme document
https://bharatsahayak-static-content-dev.s3.ap-south-1.amazonaws.com/schemes/central/pm-kisan.json

# Application form
https://bharatsahayak-static-content-dev.s3.ap-south-1.amazonaws.com/documents/application-forms/kisan-form.pdf
```

### Caching Data for Offline Access

```python
import boto3
import json

s3 = boto3.client('s3')
bucket = 'bharatsahayak-static-content-dev'

# Cache scheme data
scheme_data = {...}
s3.put_object(
    Bucket=bucket,
    Key='cache/schemes/scheme-001.json',
    Body=json.dumps(scheme_data),
    ContentType='application/json',
    Metadata={
        'cached-at': '2024-01-20T10:00:00Z',
        'expires-at': '2024-02-20T10:00:00Z'
    }
)
```

## File Naming Conventions

### Scheme Documents

- Use kebab-case: `pradhan-mantri-kisan-samman-nidhi.json`
- Include language suffix for translations: `-hi.json`, `-en.json`
- Keep names descriptive and searchable

### Application Forms

- Format: `{scheme-name}-application-form-{language}.pdf`
- Example: `pm-kisan-application-form-hi.pdf`

### Cache Files

- Format: `{type}/{id}-{timestamp}.json`
- Example: `cache/schemes/scheme-001-20240120.json`

## Security Considerations

1. **Public Access**: Only `/schemes` and `/documents` are publicly accessible
2. **Versioning**: Enabled to recover from accidental deletions or modifications
3. **Encryption**: S3 default encryption (SSE-S3) is enabled
4. **Access Logging**: Consider enabling S3 access logging for audit trails

## Cost Optimization

1. **Lifecycle Policies**: Automatically transition old cache files to cheaper storage
2. **Compression**: Compress JSON files before uploading
3. **CloudFront**: Consider adding CloudFront CDN for frequently accessed content

## Monitoring

Monitor bucket usage with CloudWatch metrics:

- `BucketSizeBytes`: Total bucket size
- `NumberOfObjects`: Total object count
- `AllRequests`: Request count
- `4xxErrors`, `5xxErrors`: Error rates

## Troubleshooting

### Bucket Not Found

```bash
# Check if bucket exists
aws s3api head-bucket --bucket bharatsahayak-static-content-dev

# If not, deploy the CloudFormation stack
sam deploy
```

### Access Denied

```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket bharatsahayak-static-content-dev

# Check public access block configuration
aws s3api get-public-access-block --bucket bharatsahayak-static-content-dev
```

### CORS Issues

```bash
# Check CORS configuration
aws s3api get-bucket-cors --bucket bharatsahayak-static-content-dev

# Update CORS if needed (defined in template.yaml)
sam deploy
```

## Related Requirements

This S3 bucket setup addresses the following requirements:

- **Requirement 7.1**: Offline functionality - cache folder stores data for offline access
- **Requirement 12.1**: Content accuracy and freshness - versioning tracks document updates

## Next Steps

1. Upload initial scheme documents
2. Configure CloudFront CDN for better performance
3. Set up automated sync from government data sources
4. Implement cache invalidation strategy
5. Add monitoring and alerting for bucket usage
