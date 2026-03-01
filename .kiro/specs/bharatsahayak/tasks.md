# Implementation Plan: BharatSahayak

## Overview

This implementation plan breaks down the BharatSahayak project into manageable tasks for a BTech student project. The focus is on building the core eligibility-checking functionality using AWS services (Lambda, API Gateway, DynamoDB, S3, Cognito) with Python. Advanced features like voice interface and multilingual support are marked as optional for later phases.

The implementation follows an incremental approach: starting with infrastructure setup, then building core data models and APIs, implementing the eligibility engine, and finally adding optional enhancements.

## Tasks

- [ ] 1. Set up AWS infrastructure and project foundation
  - [x] 1.1 Initialize Python project with AWS SAM or Serverless Framework
    - Create project structure with src/, tests/, and infrastructure directories
    - Set up requirements.txt with boto3, fastapi, pydantic, pytest
    - Configure AWS credentials and region settings
    - _Requirements: 10.1, 10.2_
  
  - [x] 1.2 Create DynamoDB tables for core data storage
    - Create Users table (partition key: user_id)
    - Create Schemes table (partition key: scheme_id, GSI on category)
    - Create UserProfiles table (partition key: user_id)
    - Create Interactions table (partition key: user_id, sort key: timestamp)
    - _Requirements: 8.1, 2.1, 9.1_
  
  - [x] 1.3 Set up S3 bucket for static content and scheme documents
    - Create S3 bucket with appropriate permissions
    - Configure bucket policies for public read access to scheme documents
    - Set up folder structure: /schemes, /documents, /cache
    - _Requirements: 7.1, 12.1_
  
  - [x] 1.4 Configure AWS Cognito for user authentication
    - Create Cognito User Pool with phone number as username
    - Configure OTP-based authentication flow
    - Set up user attributes: phone_number, preferred_language, location
    - _Requirements: 11.1, 11.2_

- [x] 2. Implement core data models and validation
  - [x] 2.1 Create Pydantic models for all data structures
    - Implement UserProfile, Location, Scheme, EligibilityCriteria models
    - Add validation rules for required fields and data types
    - Implement serialization/deserialization methods
    - _Requirements: 8.1, 2.1, 2.3_
  
  - [ ] 2.2 Write property test for data model round-trip
    - **Property 20: Profile Data Round-Trip**
    - **Validates: Requirements 8.1** 
    - Test that storing and retrieving user profiles preserves all fields
  
  - [x] 2.3 Create DynamoDB repository classes
    - Implement UserRepository with CRUD operations
    - Implement SchemeRepository with search and filter methods
    - Implement ProfileRepository with get/update operations
    - Add error handling for DynamoDB exceptions
    - _Requirements: 8.1, 2.1, 2.5_
  
  - [x] 2.4 Write unit tests for repository classes
    - Test CRUD operations with mocked DynamoDB
    - Test error handling for network failures
    - Test query filters and pagination
    - _Requirements: 8.1, 2.1_

- [x] 3. Build user registration and authentication APIs
  - [x] 3.1 Implement user registration Lambda function
    - Create Lambda handler for POST /auth/register
    - Integrate with Cognito to create user and send OTP
    - Store user profile in DynamoDB
    - Return session token on successful registration
    - _Requirements: 8.1, 11.1_
  
  - [x] 3.2 Implement OTP verification Lambda function
    - Create Lambda handler for POST /auth/verify
    - Validate OTP with Cognito
    - Generate JWT token for authenticated sessions
    - _Requirements: 11.1_
  
  - [x] 3.3 Implement user profile management Lambda functions
    - Create Lambda handler for GET /user/profile
    - Create Lambda handler for PUT /user/profile
    - Add authorization middleware to verify JWT tokens
    - _Requirements: 8.1, 8.2_
  
  - [x] 3.4 Write unit tests for authentication flow
    - Test registration with valid/invalid phone numbers
    - Test OTP verification success and failure cases
    - Test JWT token generation and validation
    - _Requirements: 11.1_

- [x] 4. Checkpoint - Ensure authentication works end-to-end
  - Test user registration, OTP verification, and profile retrieval
  - Verify DynamoDB tables are populated correctly
  - Ensure all tests pass, ask the user if questions arise

- [x] 5. Implement scheme database and search functionality
  - [x] 5.1 Create scheme data loader script
    - Write Python script to load scheme data from JSON/CSV files
    - Parse scheme information and eligibility criteria
    - Bulk insert schemes into DynamoDB Schemes table
    - Add sample schemes for testing (at least 20 schemes across categories)
    - _Requirements: 2.1, 2.5, 12.1_
  
  - [x] 5.2 Implement scheme search Lambda function
    - Create Lambda handler for GET /schemes with query parameters
    - Implement keyword search across scheme name and description
    - Add filters for category, state, and department
    - Return paginated results with scheme summaries
    - _Requirements: 2.1, 2.2_
  
  - [x] 5.3 Write property test for scheme search relevance
    - **Property 4: Scheme Search Relevance**
    - **Validates: Requirements 2.1**
    - Test that search results match query context semantically
  
  - [x] 5.4 Implement scheme details Lambda function
    - Create Lambda handler for GET /schemes/{scheme_id}
    - Return complete scheme information including eligibility criteria
    - Include application process and required documents
    - _Requirements: 2.2_
  
  - [ ] 5.5 Write property test for complete information display
    - **Property 5: Complete Information Display**
    - **Validates: Requirements 2.2**
    - Test that all required fields are present in scheme details
  
  - [x] 5.6 Write unit tests for scheme search
    - Test search with various keywords and filters
    - Test pagination and result ordering
    - Test empty results and error cases
    - _Requirements: 2.1, 2.2_

- [x] 6. Implement eligibility checking engine
  - [x] 6.1 Create EligibilityChecker class with rule evaluation logic
    - Implement check_eligibility method to evaluate all criteria
    - Add support for age range, income limits, occupation matching
    - Add support for location-based eligibility (state, district)
    - Add support for education level and gender criteria
    - Return EligibilityResult with is_eligible flag and reasoning
    - _Requirements: 2.3_
  
  - [x] 6.2 Implement eligibility check Lambda function
    - Create Lambda handler for POST /schemes/check-eligibility
    - Accept user profile and scheme_id in request body
    - Call EligibilityChecker to determine eligibility
    - Return detailed eligibility result with missing criteria
    - _Requirements: 2.3_
  
  - [x] 6.3 Write property test for eligibility determination correctness
    - **Property 6: Eligibility Determination Correctness**
    - **Validates: Requirements 2.3**
    - Test that eligibility is determined correctly for all criteria combinations
  
  - [x] 6.4 Implement bulk eligibility check Lambda function
    - Create Lambda handler for POST /schemes/eligible
    - Accept user profile and return all eligible schemes
    - Filter schemes by eligibility and rank by relevance
    - Include eligibility explanation for each scheme
    - _Requirements: 2.3, 8.2_
  
  - [x] 6.4 Write property test for personalized recommendation filtering
    - **Property 21: Personalized Recommendation Filtering**
    - **Validates: Requirements 8.2**
    - Test that different user profiles receive different recommendations
  
  - [x] 6.5 Write unit tests for eligibility checker
    - Test each eligibility criterion independently
    - Test combinations of criteria
    - Test edge cases (boundary ages, income limits)
    - Test missing profile data handling
    - _Requirements: 2.3_

- [x] 7. Checkpoint - Ensure eligibility checking works correctly
  - Test eligibility checking with various user profiles
  - Verify correct schemes are returned for different users
  - Ensure all tests pass, ask the user if questions arise

- [x] 8. Set up API Gateway and integrate Lambda functions
  - [x] 8.1 Create API Gateway REST API
    - Define API resources and methods for all endpoints
    - Configure CORS for web client access
    - Set up request/response models and validation
    - _Requirements: 10.1, 10.4_
  
  - [x] 8.2 Integrate Lambda functions with API Gateway
    - Connect all Lambda functions to API Gateway endpoints
    - Configure Lambda proxy integration
    - Set up authorization with Cognito User Pool
    - Add request throttling and rate limiting
    - _Requirements: 10.1, 10.4_
  
  - [x] 8.3 Configure API Gateway stages and deployment
    - Create dev and prod stages
    - Set up stage variables for environment configuration
    - Deploy API and test all endpoints
    - _Requirements: 10.1_
  
  - [x] 8.4 Write integration tests for API endpoints
    - Test complete request/response flow for each endpoint
    - Test authentication and authorization
    - Test error responses and status codes
    - _Requirements: 10.1, 11.1_

- [x] 9. Implement impact tracking and analytics
  - [x] 9.1 Create InteractionEvent and OutcomeEvent models
    - Define event types: query_submitted, scheme_accessed, scheme_applied
    - Add event_data field for flexible metadata storage
    - _Requirements: 9.1, 9.3_
  
  - [x] 9.2 Implement event recording Lambda function
    - Create Lambda handler for POST /impact/event
    - Store events in DynamoDB Interactions table
    - Add timestamp and user_id to all events
    - _Requirements: 9.1, 9.3_
  
  - [x] 9.3 Write property test for interaction event recording
    - **Property 23: Interaction Event Recording**
    - **Validates: Requirements 9.1, 9.3**
    - Test that all events are recorded with required fields
  
  - [x] 9.4 Implement analytics query Lambda function
    - Create Lambda handler for GET /impact with filters
    - Aggregate events by user, category, and time period
    - Calculate metrics: total users, schemes accessed, success rate
    - Anonymize user data in results
    - _Requirements: 9.2, 9.4_
  
  - [x] 9.5 Write property test for analytics data anonymization
    - **Property 25: Analytics Data Anonymization**
    - **Validates: Requirements 9.4**
    - Test that PII is not present in analytics results
  
  - [x] 9.6 Write unit tests for impact tracking
    - Test event recording with various event types
    - Test analytics aggregation and filtering
    - Test anonymization of sensitive data
    - _Requirements: 9.1, 9.2, 9.4_

- [x] 10. Build simple web interface for testing
  - [x] 10.1 Create basic HTML/JavaScript frontend
    - Build registration and login forms
    - Create user profile input form
    - Build scheme search and browse interface
    - Display eligibility results with explanations
    - _Requirements: 10.1, 10.2_
  
  - [x] 10.2 Deploy frontend to S3 with CloudFront
    - Upload static files to S3 bucket
    - Configure S3 for static website hosting
    - Set up CloudFront distribution for HTTPS access
    - _Requirements: 10.1_
  
  - [x] 10.3 Test complete user flow end-to-end
    - Test user registration and authentication
    - Test profile creation and updates
    - Test scheme search and eligibility checking
    - Test analytics event recording
    - _Requirements: 1.1-12.5_

- [ ] 11. Checkpoint - Final testing and validation
  - Ensure all core features work end-to-end
  - Verify data persistence in DynamoDB
  - Test error handling and edge cases
  - Ensure all tests pass, ask the user if questions arise
 
- [ ] 12. Optional: Add agricultural advisory features
  - [ ]* 12.1 Create FarmProfile model and DynamoDB table
    - Define farm attributes: land_size, soil_type, irrigation, location
    - Create DynamoDB table for farm profiles
    - _Requirements: 3.1_
  
  - [ ]* 12.2 Implement crop recommendation Lambda function
    - Create Lambda handler for POST /farmer/crop-advice
    - Implement basic crop recommendation logic based on season and soil
    - Return crop suggestions with reasoning
    - _Requirements: 3.1_
  
  - [ ]* 12.3 Write property test for crop recommendation generation
    - **Property 7: Crop Recommendation Generation**
    - **Validates: Requirements 3.1**
    - Test that recommendations contain all required fields
  
  - [ ]* 12.4 Integrate external mandi price API
    - Research and integrate government mandi price API
    - Create Lambda handler for GET /farmer/market-price
    - Cache prices in DynamoDB for offline access
    - _Requirements: 3.3_
  
  - [ ]* 12.5 Write property test for mandi price radius constraint
    - **Property 9: Mandi Price Radius Constraint**
    - **Validates: Requirements 3.3**
    - Test that returned prices are within specified radius

- [ ] 13. Optional: Add skill development and job matching
  - [ ]* 13.1 Create SkillProgram and JobPosting models
    - Define skill program attributes and eligibility
    - Define job posting attributes and qualifications
    - Create DynamoDB tables for programs and jobs
    - _Requirements: 4.1, 4.3_
  
  - [ ]* 13.2 Load sample skill programs and job postings
    - Create data loader script for programs and jobs
    - Add at least 10 sample programs and 10 job postings
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 13.3 Implement skill program matching Lambda function
    - Create Lambda handler for POST /skills/match
    - Match programs based on user education and interests
    - Return ranked list of relevant programs
    - _Requirements: 4.1_
  
  - [ ]* 13.4 Write property test for skill program matching relevance
    - **Property 10: Skill Program Matching Relevance**
    - **Validates: Requirements 4.1**
    - Test that matched programs align with user profile
  
  - [ ]* 13.5 Implement job search Lambda function
    - Create Lambda handler for GET /jobs with filters
    - Filter jobs by qualifications and location
    - Return jobs matching user education level
    - _Requirements: 4.3_
  
  - [ ]* 13.6 Write property test for job qualification matching
    - **Property 11: Job Search Qualification Matching**
    - **Validates: Requirements 4.3**
    - Test that returned jobs match user qualifications

- [ ] 14. Optional: Add health advisory features
  - [ ]* 14.1 Create HealthFacility model and DynamoDB table
    - Define facility attributes: name, type, location, services
    - Create DynamoDB table with geospatial index
    - Load sample health facility data
    - _Requirements: 5.2_
  
  - [ ]* 14.2 Implement health facility search Lambda function
    - Create Lambda handler for GET /health/facilities
    - Search facilities by location and radius
    - Calculate distances and sort by proximity
    - _Requirements: 5.2_
  
  - [ ]* 14.3 Write property test for health facility distance accuracy
    - **Property 13: Health Facility Distance Accuracy**
    - **Validates: Requirements 5.2**
    - Test that facilities are within radius and sorted correctly
  
  - [ ]* 14.4 Implement basic symptom checker Lambda function
    - Create Lambda handler for POST /health/check
    - Implement rule-based symptom analysis
    - Return health guidance with urgency level and disclaimer
    - _Requirements: 5.1, 5.3_
  
  - [ ]* 14.5 Write property test for health guidance generation
    - **Property 12: Health Guidance Generation**
    - **Validates: Requirements 5.1**
    - Test that guidance contains all required fields
  
  - [ ]* 14.6 Write property test for health disclaimer presence
    - **Property 14: Health Disclaimer Presence**
    - **Validates: Requirements 5.3**
    - Test that all health responses include disclaimer
  
  - [ ]* 14.7 Write property test for emergency symptom detection
    - **Property 29: Emergency Symptom Detection**
    - **Validates: Requirements 5.5**
    - Test that emergency symptoms trigger urgent care recommendation

- [ ] 15. Optional: Add voice interface with AWS services
  - [ ]* 15.1 Integrate Amazon Transcribe for speech-to-text
    - Create Lambda function to process audio uploads
    - Use Amazon Transcribe for Hindi and English
    - Return transcribed text with confidence scores
    - _Requirements: 1.1_
  
  - [ ]* 15.2 Write property test for voice-to-text accuracy
    - **Property 1: Voice-to-Text Transcription Accuracy**
    - **Validates: Requirements 1.1**
    - Test transcription accuracy with sample audio files
  
  - [ ]* 15.3 Integrate Amazon Polly for text-to-speech
    - Create Lambda function to generate speech from text
    - Use Amazon Polly with Hindi and English voices
    - Return audio file URL from S3
    - _Requirements: 1.2_
  
  - [ ]* 15.4 Write property test for text-to-speech generation
    - **Property 2: Text-to-Speech Audio Generation**
    - **Validates: Requirements 1.2**
    - Test that valid audio is generated for all text inputs
  
  - [ ]* 15.5 Implement language detection with Amazon Comprehend
    - Use Amazon Comprehend to detect spoken language
    - Support Hindi, English, and major regional languages
    - _Requirements: 1.3_
  
  - [ ]* 15.6 Write property test for language detection accuracy
    - **Property 3: Language Detection Accuracy**
    - **Validates: Requirements 1.3**
    - Test language detection with multilingual samples

- [ ] 16. Optional: Add multilingual support with Amazon Translate
  - [ ]* 16.1 Integrate Amazon Translate for scheme translations
    - Create Lambda function to translate scheme content
    - Cache translations in DynamoDB for performance
    - Support Hindi, English, and 2-3 regional languages
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 16.2 Update API responses to include translations
    - Modify scheme APIs to return content in requested language
    - Add language parameter to all relevant endpoints
    - Fall back to English if translation unavailable
    - _Requirements: 1.1_
  
  - [ ]* 16.3 Test multilingual functionality end-to-end
    - Test scheme search and display in multiple languages
    - Test voice interface with Hindi audio
    - Verify translation quality and accuracy
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 17. Optional: Implement offline caching with DynamoDB and S3
  - [ ]* 17.1 Create offline cache data export Lambda function
    - Export frequently accessed schemes to JSON files
    - Store cache files in S3 for download
    - Include timestamp and version information
    - _Requirements: 7.1, 7.3_
  
  - [ ]* 17.2 Write property test for offline cache priority
    - **Property 19: Offline Cache Priority**
    - **Validates: Requirements 7.3**
    - Test that high-priority content is cached first
  
  - [ ]* 17.3 Implement cache sync Lambda function
    - Create endpoint to check for cache updates
    - Return list of updated schemes since last sync
    - Support incremental updates to minimize bandwidth
    - _Requirements: 7.4_
  
  - [ ]* 17.4 Write property test for bandwidth constraint compliance
    - **Property 18: Bandwidth Constraint Compliance**
    - **Validates: Requirements 7.2**
    - Test that API responses are under 100KB when compressed

- [ ] 18. Optional: Add RAG-based conversational AI
  - [ ]* 18.1 Set up vector database with Amazon OpenSearch
    - Create OpenSearch domain for document embeddings
    - Index scheme documents with vector embeddings
    - Configure search with semantic similarity
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 18.2 Integrate with Amazon Bedrock for LLM
    - Use Bedrock to access foundation models (Claude, Llama)
    - Implement RAG pipeline: retrieve → augment → generate
    - Maintain conversation context across turns
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 18.3 Write property test for conversation context preservation
    - **Property 15: Conversation Context Preservation**
    - **Validates: Requirements 6.1**
    - Test that follow-up queries maintain context
  
  - [ ]* 18.4 Write property test for semantic search relevance
    - **Property 16: Semantic Search Relevance**
    - **Validates: Requirements 6.2**
    - Test that retrieved documents have high similarity scores
  
  - [ ]* 18.5 Implement conversational query Lambda function
    - Create Lambda handler for POST /ask
    - Process natural language queries with RAG
    - Return AI-generated responses with source citations
    - _Requirements: 6.1, 6.2, 6.5_
  
  - [ ]* 18.6 Write property test for official source prioritization
    - **Property 17: Official Source Prioritization**
    - **Validates: Requirements 6.5**
    - Test that government sources rank higher than general sources

## Notes

- Tasks marked with `*` are optional and can be implemented in later phases
- Core functionality (tasks 1-11) should be completed first for MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for user feedback
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Focus on AWS services throughout: Lambda, API Gateway, DynamoDB, S3, Cognito
- Advanced features (voice, multilingual, RAG) are optional for BTech project scope
- The implementation is designed to be completed within a semester timeframe
 