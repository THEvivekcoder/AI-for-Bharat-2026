# BharatSahayak Frontend - Testing Interface

A simple, minimal web interface for testing the BharatSahayak backend APIs.

## Features

- **API Configuration**: Configure API Gateway endpoint and Cognito credentials
- **User Authentication**: Register new users and login with OTP verification
- **Profile Management**: Create and update user profiles with demographic information
- **Scheme Search**: Search and browse government schemes by keywords, category, and state
- **Eligibility Checking**: Check eligibility for specific schemes or get all eligible schemes
- **Analytics**: Record events and view impact metrics

## Setup Instructions

### 1. Configure API Endpoint

After deploying the backend infrastructure:

1. Get your API Gateway endpoint URL from AWS CloudFormation outputs
2. Get your Cognito User Pool ID and Client ID from CloudFormation outputs
3. Open `index.html` in a web browser
4. Fill in the configuration section with your values
5. Click "Save Configuration"

### 2. Test User Flow

#### Registration and Login
1. Enter a phone number (format: +919876543210)
2. Select preferred language
3. Click "Register"
4. Check your phone for OTP (in dev environment, check CloudWatch logs)
5. Enter OTP and click "Verify & Login"

#### Profile Management
1. After login, the profile section will appear
2. Fill in your demographic information (age, gender, education, occupation, income, location)
3. Click "Update Profile"

#### Search Schemes
1. Enter search keywords (e.g., "agriculture", "education")
2. Optionally filter by category and state
3. Click "Search Schemes"
4. View scheme details or check eligibility directly from results

#### Check Eligibility
1. Ensure your profile is filled out
2. Enter a scheme ID or select from search results
3. Click "Check Eligibility" to see if you qualify
4. Or click "Get All Eligible Schemes" to see all schemes you qualify for

#### Analytics
1. Record events to track usage
2. View analytics to see impact metrics

## File Structure

```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # Styling and layout
├── app.js          # JavaScript functionality
└── README.md       # This file
```

## Deployment Options

### Option 1: Local Testing
Simply open `index.html` in a web browser. Works for testing with deployed backend APIs.

### Option 2: S3 Static Website Hosting
1. Upload all files to your S3 bucket
2. Enable static website hosting on the bucket
3. Set `index.html` as the index document
4. Access via S3 website endpoint

### Option 3: CloudFront Distribution
1. Upload files to S3
2. Create a CloudFront distribution pointing to the S3 bucket
3. Access via CloudFront URL for HTTPS and better performance

## API Endpoints Used

- `POST /auth/register` - User registration
- `POST /auth/verify` - OTP verification
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile
- `GET /schemes` - Search schemes
- `GET /schemes/{scheme_id}` - Get scheme details
- `POST /schemes/check-eligibility` - Check eligibility for a scheme
- `POST /schemes/eligible` - Get all eligible schemes
- `POST /impact/event` - Record analytics event
- `GET /impact` - Get analytics data

## Browser Compatibility

Works on all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Notes

- This is a **testing interface**, not a production-ready UI
- No advanced error handling or validation
- Minimal styling for functionality focus
- All data is stored in browser localStorage for convenience
- CORS must be enabled on API Gateway for cross-origin requests

## Troubleshooting

### "Please configure API endpoint first"
- Make sure you've saved the configuration with valid API endpoint and Cognito details

### "Failed to fetch" errors
- Check that API Gateway CORS is properly configured
- Verify the API endpoint URL is correct (no trailing slash)
- Check browser console for detailed error messages

### OTP not received
- In dev environment, OTPs are logged to CloudWatch
- Check Lambda function logs for the OTP code
- Ensure Cognito SMS configuration is set up correctly

### Authentication errors
- Verify Cognito User Pool ID and Client ID are correct
- Check that the user is confirmed in Cognito
- Try logging out and logging in again

## Future Enhancements

For a production version, consider adding:
- Form validation and better error handling
- Loading states and spinners
- Responsive design improvements
- Accessibility features (ARIA labels, keyboard navigation)
- Internationalization (i18n) for multiple languages
- Voice interface integration
- Offline support with service workers
- Progressive Web App (PWA) features
