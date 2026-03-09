// Configuration for BharatSahayak Modern UI

const CONFIG = {
  // API Configuration
  api: {
    baseURL: 'https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev',
    timeout: 30000
  },
  
  // AWS Cognito Configuration
  cognito: {
    userPoolId: 'ap-south-1_KSJ0FKz20',
    clientId: '10emq71eioca5qkns6on0l22om',
    region: 'ap-south-1'
  },
  
  // S3 Configuration
  s3: {
    staticContentBucket: 'bharatsahayak-static-content-dev',
    staticContentURL: 'https://bharatsahayak-static-content-dev.s3.ap-south-1.amazonaws.com',
    region: 'ap-south-1'
  },
  
  // Feature Flags
  features: {
    voiceInterface: true,
    offlineMode: true,
    multilingualSupport: true,
    guestMode: true
  },
  
  // Supported Languages
  languages: [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi' },
    { code: 'bn', name: 'Bengali' },
    { code: 'te', name: 'Telugu' },
    { code: 'mr', name: 'Marathi' },
    { code: 'ta', name: 'Tamil' },
    { code: 'gu', name: 'Gujarati' },
    { code: 'kn', name: 'Kannada' },
    { code: 'ml', name: 'Malayalam' },
    { code: 'pa', name: 'Punjabi' }
  ],
  
  // App Metadata
  app: {
    name: 'BharatSahayak',
    version: '1.0.0',
    description: 'AI-Powered Government Scheme Finder',
    supportEmail: 'support@bharatsahayak.in',
    supportPhone: '1800-123-4567'
  }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
}
