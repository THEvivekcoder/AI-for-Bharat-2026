# Quick Start Guide

## Running Locally (Development)

### Option 1: Using Node.js Server (Recommended)
```bash
cd modern-ui
node server.js
```
Then open: `http://localhost:8080`

### Option 2: Using Python Server
```bash
cd modern-ui
python -m http.server 8080
```
Then open: `http://localhost:8080`

### Option 3: Using Live Server (VS Code Extension)
1. Install "Live Server" extension in VS Code
2. Right-click `index.html` → "Open with Live Server"

## Why Local Server is Required

Opening HTML files directly (`file://` protocol) causes CORS errors when making API calls to AWS. A local server (`http://localhost`) allows proper CORS handling.

## Deploying to S3 (Production)

### Step 1: Convert CSV to JavaScript
```bash
cd modern-ui
node js/convert-csv.js
```

### Step 2: Deploy to S3
```bash
aws s3 sync . s3://bharatsahayak-static-content-dev/modern-ui/ \
  --region ap-south-1 \
  --exclude "*.sh" \
  --exclude "*.md" \
  --exclude "server.js" \
  --exclude "convert-csv.js" \
  --exclude "node_modules/*"
```

### Step 3: Update Bucket Policy
Add this to your bucket policy:
```json
{
  "Sid": "PublicReadModernUI",
  "Effect": "Allow",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::bharatsahayak-static-content-dev/modern-ui/*"
}
```

### Step 4: Access Your App
```
https://bharatsahayak-static-content-dev.s3.ap-south-1.amazonaws.com/modern-ui/index.html
```

## Troubleshooting

### "Failed to fetch" Error
- **Cause**: Opening files directly or CORS issues
- **Fix**: Use local server (Option 1, 2, or 3 above)

### API Errors
- Check browser console (F12) for detailed error logs
- Verify API endpoint is correct in `config.js`
- Test API directly: `curl https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev/schemes`

### Schemes Not Loading
- Check if `schemes-data.js` exists
- Run `node js/convert-csv.js` to regenerate
- Verify CSV file exists at `../data/updated_data.csv`
