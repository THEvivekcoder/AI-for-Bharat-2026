// Configuration for BharatSahayak Modern UI

const CONFIG = {
  // API Configuration
  api: {
    baseURL: 'https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev',
    timeout: 30000
  },
  
  // S3 Configuration
  s3: {
    staticContentBucket: 'bharatsahayak-static-390402557080-dev',
    staticContentURL: 'https://bharatsahayak-static-390402557080-dev.s3.us-east-1.amazonaws.com',
    region: 'us-east-1'
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
