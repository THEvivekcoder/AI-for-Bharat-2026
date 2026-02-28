# Implementation Plan: BharatSahayak

## Overview

This implementation plan breaks down the BharatSahayak multilingual AI assistant into discrete, manageable coding tasks. The approach follows an incremental development strategy, building core infrastructure first, then adding domain services, and finally integrating all components. Each task builds upon previous work, with checkpoints to ensure stability before proceeding.

The implementation uses Python for the backend (FastAPI), with support for AI/ML libraries (transformers, langchain, FAISS), voice processing (Whisper, Coqui TTS), and multilingual NLP (IndicTrans, Bhashini).

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create Python project with FastAPI backend
  - Set up virtual environment and dependencies (fastapi, uvicorn, sqlalchemy, pydantic)
  - Configure PostgreSQL database connection
  - Create base data models (User, Location, UserProfile)
  - Set up Redis for caching
  - Configure logging and error handling middleware
  - Create health check endpoint (GET /health)
  - _Requirements: 11.1, 11.2_

- [ ]* 1.1 Write unit tests for core infrastructure
  - Test database connection and models
  - Test Redis caching
  - Test health check endpoint
  - _Requirements: 11.1, 11.2_

- [ ] 2. Implement authentication and user management
  - [x] 2.1 Create User Manager service
    - Implement user registration with phone number
    - Implement OTP generation and verification
    - Implement JWT token generation and validation
    - Create user profile CRUD operations
    - _Requirements: 11.1, 11.4_

  - [x] 2.2 Create authentication endpoints
    - POST /api/auth/register - Register new user
    - POST /api/auth/verify - Verify OTP and authenticate
    - GET /api/user/profile - Get user profile
    - PUT /api/user/profile - Update user profile
    - DELETE /api/user/data - Delete user data
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 2.3 Write property test for profile data persistence
    - **Property 20: Profile Data Round-Trip**
    - **Validates: Requirements 8.1**

  - [ ]* 2.4 Write unit tests for authentication
    - Test OTP generation and validation
    - Test JWT token creation and verification
    - Test profile CRUD operations
    - Test data deletion completeness
    - _Requirements: 11.1, 11.3, 11.4_

- [x] 3. Checkpoint - Ensure authentication and user management work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement voice interface module
  - [x] 4.1 Set up Speech-to-Text engine
    - Integrate Whisper model for STT
    - Implement audio preprocessing (noise reduction, normalization)
    - Implement language detection
    - Create transcription function with confidence scoring
    - _Requirements: 1.1, 1.3_

  - [x] 4.2 Set up Text-to-Speech engine
    - Integrate Coqui TTS or Indic TTS for supported languages
    - Implement voice synthesis for Hindi and regional languages
    - Create audio generation function
    - _Requirements: 1.2_

  - [x] 4.3 Create voice interface endpoints
    - POST /api/voice-to-text - Upload audio, receive transcription
    - POST /api/text-to-voice - Send text, receive audio
    - GET /api/languages - List supported languages
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.4 Write property test for STT accuracy
    - **Property 1: Voice-to-Text Transcription Accuracy**
    - **Validates: Requirements 1.1**

  - [x] 4.5 Write property test for TTS generation
    - **Property 2: Text-to-Speech Audio Generation**
    - **Validates: Requirements 1.2**

  - [x] 4.6 Write property test for language detection
    - **Property 3: Language Detection Accuracy**
    - **Validates: Requirements 1.3**

  - [x] 4.7 Write unit tests for voice interface
    - Test audio format validation
    - Test error handling for poor quality audio
    - Test unsupported language handling
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Implement RAG engine and LLM core
  - [x] 5.1 Set up vector database
    - Initialize FAISS vector store
    - Create embedding model (sentence-transformers)
    - Implement document ingestion and indexing
    - Create semantic search function
    - _Requirements: 6.2_

  - [x] 5.2 Implement RAG Engine
    - Create RAG query processing pipeline
    - Implement context retrieval (top-k documents)
    - Integrate LLM (LLaMA/Mistral/GPT) for response generation
    - Implement prompt construction with retrieved context
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 5.3 Implement Conversation Manager
    - Create session management (create, get, update, delete)
    - Implement conversation context storage (Redis)
    - Implement context preservation across turns
    - _Requirements: 6.1_

  - [x] 5.4 Create RAG and conversation endpoints
    - POST /api/ask - Submit query, receive AI response
    - POST /api/session/create - Create conversation session
    - DELETE /api/session/{session_id} - Clear session
    - _Requirements: 6.1, 6.2_

  - [x] 5.5 Write property test for context preservation
    - **Property 15: Conversation Context Preservation**
    - **Validates: Requirements 6.1**

  - [x] 5.6 Write property test for semantic search relevance
    - **Property 16: Semantic Search Relevance**
    - **Validates: Requirements 6.2**

  - [x] 5.7 Write property test for source prioritization
    - **Property 17: Official Source Prioritization**
    - **Validates: Requirements 6.5**

  - [x] 5.8 Write unit tests for RAG engine
    - Test document ingestion
    - Test query processing with empty context
    - Test out-of-scope query handling
    - _Requirements: 6.1, 6.2, 6.4_

- [ ] 6. Checkpoint - Ensure voice and AI core functionality work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Scheme Service
  - [x] 7.1 Create Scheme data models and database schema
    - Create Scheme, EligibilityCriteria models
    - Create scheme_translations table
    - Implement database migrations
    - _Requirements: 2.1, 2.2_

  - [x] 7.2 Implement Scheme Repository
    - Create search_schemes function with filters
    - Create get_scheme_by_id function
    - Create get_all_schemes function
    - Implement scheme update function
    - _Requirements: 2.1_

  - [x] 7.3 Implement Eligibility Checker
    - Create check_eligibility function with criteria evaluation
    - Implement get_eligible_schemes function
    - Create explain_eligibility function for human-readable output
    - _Requirements: 2.3_

  - [x] 7.4 Create Scheme Service endpoints
    - GET /api/schemes - List all schemes with filters
    - GET /api/schemes/{id} - Get scheme details
    - POST /api/schemes/check-eligibility - Check eligibility
    - POST /api/schemes/eligible - Get all eligible schemes
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 7.5 Write property test for scheme search relevance
    - **Property 4: Scheme Search Relevance**
    - **Validates: Requirements 2.1, 5.4**

  - [x] 7.6 Write property test for complete information display
    - **Property 5: Complete Information Display**
    - **Validates: Requirements 2.2, 4.2**

  - [x] 7.7 Write property test for eligibility determination
    - **Property 6: Eligibility Determination Correctness**
    - **Validates: Requirements 2.3**

  - [x] 7.8 Write unit tests for Scheme Service
    - Test scheme search with various filters
    - Test eligibility with edge cases (missing criteria)
    - Test scheme not found error handling
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 8. Implement Farmer Advisory Service
  - [x] 8.1 Create Farm Profile and Crop data models
    - Create FarmProfile, CropRecommendation, FertilizerRecommendation models
    - Create crop database schema
    - _Requirements: 3.1, 3.2_

  - [x] 8.2 Implement Crop Advisor
    - Create recommend_crops function with suitability scoring
    - Implement get_crop_calendar function
    - Integrate weather data for recommendations
    - _Requirements: 3.1_

  - [x] 8.3 Implement Fertilizer Advisor
    - Create recommend_fertilizer function
    - Implement nutrient requirement calculations
    - _Requirements: 3.2_

  - [x] 8.4 Implement Mandi Price Service
    - Create get_current_price function with radius filtering
    - Implement get_price_trend function
    - Integrate with government mandi price APIs
    - Implement caching for price data
    - _Requirements: 3.3_

  - [x] 8.5 Create Farmer Advisory endpoints
    - POST /api/farmer/crop-advice - Get crop recommendations
    - POST /api/farmer/fertilizer-advice - Get fertilizer guidance
    - GET /api/farmer/market-price - Get mandi prices
    - GET /api/farmer/crop-calendar - Get crop calendar
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 8.6 Write property test for crop recommendations
    - **Property 7: Crop Recommendation Generation**
    - **Validates: Requirements 3.1**

  - [x] 8.7 Write property test for fertilizer guidance
    - **Property 8: Fertilizer Guidance Completeness**
    - **Validates: Requirements 3.2**

  - [x] 8.8 Write property test for mandi price radius
    - **Property 9: Mandi Price Radius Constraint**
    - **Validates: Requirements 3.3**

  - [x] 8.9 Write unit test for missing price data handling
    - **Property 30: Missing Market Price Handling**
    - **Validates: Requirements 3.5**

  - [x] 8.10 Write unit tests for Farmer Advisory
    - Test crop recommendations with various soil types
    - Test fertilizer guidance edge cases
    - Test price lookup with no nearby mandis
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 9. Checkpoint - Ensure scheme and farmer services work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Skills and Employment Service
  - [x] 10.1 Create Skill Program and Job data models
    - Create SkillProgram, JobPosting models
    - Create database schema for skills and jobs
    - _Requirements: 4.1, 4.3_

  - [x] 10.2 Implement Skills Matcher
    - Create match_programs function with relevance scoring
    - Implement get_program_details function
    - _Requirements: 4.1_

  - [x] 10.3 Implement Job Matcher
    - Create search_jobs function with qualification matching
    - Implement get_job_alerts function
    - _Requirements: 4.3_

  - [x] 10.4 Create Skills and Employment endpoints
    - GET /api/skills - List skill development programs
    - POST /api/skills/match - Get personalized recommendations
    - GET /api/jobs - Search government jobs
    - POST /api/jobs/alerts - Get job alerts
    - _Requirements: 4.1, 4.3_

  - [x] 10.5 Write property test for skill program matching
    - **Property 10: Skill Program Matching Relevance**
    - **Validates: Requirements 4.1**

  - [x] 10.6 Write property test for job qualification matching
    - **Property 11: Job Search Qualification Matching**
    - **Validates: Requirements 4.3**

  - [x] 10.7 Write unit tests for Skills Service
    - Test program matching with various profiles
    - Test job search with different qualifications
    - Test edge cases (no matching programs/jobs)
    - _Requirements: 4.1, 4.3_

- [x] 11. Implement Health Advisory Service
  - [x] 11.1 Create Health data models
    - Create HealthGuidance, HealthFacility, SymptomData models
    - Create health facilities database schema
    - _Requirements: 5.1, 5.2_

  - [x] 11.2 Implement Health Advisor
    - Create analyze_symptoms function with urgency classification
    - Implement emergency symptom detection
    - Create find_facilities function with distance calculation
    - _Requirements: 5.1, 5.2_

  - [x] 11.3 Create Health Advisory endpoints
    - POST /api/health/check - Submit symptoms, receive guidance
    - GET /api/health/facilities - Find nearby health facilities
    - GET /api/health/schemes - Get health insurance schemes
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 11.4 Write property test for health guidance generation
    - **Property 12: Health Guidance Generation**
    - **Validates: Requirements 5.1**

  - [x] 11.5 Write property test for facility distance accuracy
    - **Property 13: Health Facility Distance Accuracy**
    - **Validates: Requirements 5.2**

  - [x] 11.6 Write property test for disclaimer presence
    - **Property 14: Health Disclaimer Presence**
    - **Validates: Requirements 5.3**

  - [x] 11.7 Write unit test for emergency symptom detection
    - **Property 29: Emergency Symptom Detection**
    - **Validates: Requirements 5.5**

  - [x] 11.8 Write unit tests for Health Service
    - Test symptom analysis with various inputs
    - Test facility search with different locations
    - Test edge cases (no facilities nearby)
    - _Requirements: 5.1, 5.2, 5.5_

- [x] 12. Implement Language Processing Module
  - [x] 12.1 Set up translation and NLP models
    - Integrate IndicTrans for Indic language translation
    - Set up Bhashini API integration (if using cloud)
    - Implement language detection
    - _Requirements: 1.3_

  - [x] 12.2 Implement Language Processor
    - Create translate function for supported languages
    - Implement romanization function
    - Create transliteration function
    - _Requirements: 1.3_

  - [x] 12.3 Create Language Processing endpoints
    - POST /api/translate - Translate text
    - POST /api/detect-language - Detect language
    - POST /api/transliterate - Convert between scripts
    - _Requirements: 1.3_

  - [x] 12.4 Write unit tests for Language Processing
    - Test translation between language pairs
    - Test language detection accuracy
    - Test transliteration edge cases
    - _Requirements: 1.3_

- [x] 13. Checkpoint - Ensure all domain services work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Implement Impact Tracking Service
  - [x] 14.1 Create Impact Tracker data models
    - Create InteractionEvent, OutcomeEvent, ImpactMetrics models
    - Create analytics database schema
    - _Requirements: 9.1, 9.3_

  - [x] 14.2 Implement Impact Tracker
    - Create record_interaction function
    - Create record_outcome function
    - Implement get_metrics function with aggregation
    - Implement generate_report function
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 14.3 Create Impact Tracking endpoints
    - POST /api/impact/event - Record interaction or outcome
    - GET /api/impact - Get impact metrics with filters
    - GET /api/impact/report - Generate impact report
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 14.4 Write property test for event recording
    - **Property 23: Interaction Event Recording**
    - **Validates: Requirements 9.1, 9.3**

  - [x] 14.5 Write property test for metrics aggregation
    - **Property 24: Impact Metrics Aggregation**
    - **Validates: Requirements 9.2**

  - [x] 14.6 Write property test for data anonymization
    - **Property 25: Analytics Data Anonymization**
    - **Validates: Requirements 9.4**

  - [x] 14.7 Write unit tests for Impact Tracker
    - Test event recording with various event types
    - Test aggregation with different filters
    - Test anonymization completeness
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 15. Implement Offline Cache Manager
  - [x] 15.1 Set up SQLite for offline storage
    - Create SQLite database schema for cached content
    - Create CacheManager class
    - _Requirements: 7.1, 7.3_

  - [x] 15.2 Implement Cache Manager
    - Create cache_content function with priority handling
    - Implement get_cached_content function
    - Create sync_with_server function
    - Implement invalidate_cache function
    - _Requirements: 7.1, 7.3, 7.4_

  - [x] 15.3 Implement offline mode detection and fallback
    - Create network connectivity checker
    - Implement automatic fallback to cached data
    - Create sync trigger on reconnection
    - _Requirements: 7.1, 7.4_

  - [x] 15.4 Write property test for bandwidth compliance
    - **Property 18: Bandwidth Constraint Compliance**
    - **Validates: Requirements 7.2**

  - [x] 15.5 Write property test for cache priority
    - **Property 19: Offline Cache Priority**
    - **Validates: Requirements 7.3**

  - [x] 15.6 Write unit tests for Cache Manager
    - Test cache storage and retrieval
    - Test sync with conflicts
    - Test cache eviction
    - Test offline mode examples
    - _Requirements: 7.1, 7.3, 7.4_

- [x] 16. Implement personalization and recommendation engine
  - [x] 16.1 Create recommendation scoring algorithms
    - Implement relevance scoring for schemes
    - Implement relevance scoring for jobs
    - Implement relevance scoring for skill programs
    - _Requirements: 8.2_

  - [x] 16.2 Integrate personalization into services
    - Update Scheme Service to use user profile for ranking
    - Update Skills Service to use user profile for matching
    - Update Job Service to use user profile for filtering
    - _Requirements: 8.2_

  - [x] 16.3 Implement recommendation explanations
    - Create explanation generation for scheme recommendations
    - Create explanation generation for job recommendations
    - Create explanation generation for skill recommendations
    - _Requirements: 8.4_

  - [x] 16.4 Write property test for personalized filtering
    - **Property 21: Personalized Recommendation Filtering**
    - **Validates: Requirements 8.2**

  - [x] 16.5 Write property test for explanation presence
    - **Property 22: Recommendation Explanation Presence**
    - **Validates: Requirements 8.4**

  - [x] 16.6 Write unit tests for personalization
    - Test recommendation scoring with various profiles
    - Test explanation generation
    - _Requirements: 8.2, 8.4_

- [x] 17. Implement data freshness and verification tracking
  - [x] 17.1 Add timestamp tracking to all data models
    - Add last_updated field to Scheme model
    - Add last_updated field to MandiPrice model
    - Add last_updated field to JobPosting model
    - _Requirements: 12.1, 12.5_

  - [x] 17.2 Implement verification tracking
    - Create verification status field for schemes
    - Implement source attribution for unverified data
    - Create uncertainty indicators
    - _Requirements: 12.1, 12.3_

  - [x] 17.3 Write property test for freshness tracking
    - **Property 26: Scheme Data Freshness Tracking**
    - **Validates: Requirements 12.1**

  - [x] 17.4 Write property test for unverified indicators
    - **Property 27: Unverified Information Indicators**
    - **Validates: Requirements 12.3**

  - [x] 17.5 Write property test for timestamp presence
    - **Property 28: Time-Sensitive Data Timestamps**
    - **Validates: Requirements 12.5**

  - [x] 17.6 Write unit tests for data freshness
    - Test timestamp updates
    - Test verification status tracking
    - _Requirements: 12.1, 12.3, 12.5_

- [x] 18. Checkpoint - Ensure offline, personalization, and tracking work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Implement security and encryption
  - [x] 19.1 Set up TLS/HTTPS configuration
    - Configure FastAPI for HTTPS
    - Set up TLS 1.3 certificates
    - _Requirements: 11.1_

  - [x] 19.2 Implement data encryption at rest
    - Create encryption utilities using AES-256
    - Encrypt PII fields in user profiles
    - Encrypt sensitive data in database
    - _Requirements: 11.2_

  - [x] 19.3 Implement role-based access control
    - Create role definitions (user, admin, analyst)
    - Implement permission checks on endpoints
    - Create audit logging for data access
    - _Requirements: 11.4_

  - [x] 19.4 Write unit tests for security
    - Test TLS configuration
    - Test encryption/decryption
    - Test access control
    - Test audit logging
    - _Requirements: 11.1, 11.2, 11.4_

- [x] 20. Implement error handling and rate limiting
  - [x] 20.1 Create error response models
    - Define error response format for each error category
    - Implement error translation for multilingual errors
    - _Requirements: All error handling requirements_

  - [x] 20.2 Implement rate limiting
    - Set up rate limiting middleware
    - Configure limits per endpoint
    - Implement quota tracking
    - _Requirements: API stability_

  - [x] 20.3 Add comprehensive error handling
    - Add try-catch blocks to all endpoints
    - Implement graceful degradation
    - Add retry logic for external APIs
    - _Requirements: All error handling requirements_

  - [x] 20.4 Write unit tests for error handling
    - Test each error category
    - Test rate limiting
    - Test graceful degradation
    - _Requirements: All error handling requirements_

- [x] 21. Create Progressive Web App frontend
  - [x] 21.1 Set up PWA structure
    - Create HTML/CSS/JavaScript structure
    - Configure service workers for offline support
    - Set up manifest.json for PWA
    - _Requirements: 10.2_

  - [x] 21.2 Implement voice interface UI
    - Create voice recording component
    - Create audio playback component
    - Implement language selector
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 21.3 Implement chat interface
    - Create conversation UI
    - Implement message display
    - Add loading states
    - _Requirements: 6.1_

  - [x] 21.4 Implement service-specific UIs
    - Create scheme search and display UI
    - Create farmer advisory UI
    - Create skills and jobs UI
    - Create health advisory UI
    - _Requirements: 2.1, 3.1, 4.1, 5.1_

  - [x] 21.5 Implement offline mode UI
    - Add offline indicator
    - Implement cached content display
    - Add sync status indicator
    - _Requirements: 7.1, 7.4_

  - [x] 21.6 Write integration tests for PWA
    - Test offline functionality
    - Test service worker caching
    - Test voice interface integration
    - _Requirements: 10.2, 7.1_

- [x] 22. Checkpoint - Ensure security, error handling, and PWA work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Data seeding and integration
  - [x] 23.1 Create data seeding scripts
    - Create script to seed government schemes
    - Create script to seed health facilities
    - Create script to seed skill programs
    - Create script to seed crop data
    - _Requirements: 2.1, 3.1, 4.1, 5.2_

  - [x] 23.2 Integrate with external APIs
    - Integrate with government scheme APIs
    - Integrate with mandi price APIs
    - Integrate with weather APIs
    - Set up API key management
    - _Requirements: 2.5, 3.3, 3.4_

  - [x] 23.3 Set up vector database with initial documents
    - Ingest government scheme documents
    - Ingest agricultural guidance documents
    - Ingest health information documents
    - Create embeddings and index
    - _Requirements: 6.2_

  - [x] 23.4 Write integration tests for external APIs
    - Test scheme API integration
    - Test mandi price API integration
    - Test weather API integration
    - _Requirements: 2.5, 3.3_

- [-] 24. End-to-end integration and testing
  - [x] 24.1 Wire all components together 
    - Connect voice interface to RAG engine
    - Connect RAG engine to domain services
    - Connect domain services to impact tracker
    - Ensure all endpoints work end-to-end
    - _Requirements: All requirements_

  - [x] 24.2 Write end-to-end integration tests
    - Test voice query → STT → RAG → Response → TTS flow
    - Test user registration → profile → personalized recommendations flow
    - Test offline mode → cache → sync flow
    - Test scheme search → eligibility → application guidance flow
    - _Requirements: All requirements_

  - [x] 24.3 Write performance tests
    - Test concurrent user load (1000+ users)
    - Test response time (< 3 seconds for 95th percentile)
    - Test voice processing latency
    - Test low-resource device performance
    - _Requirements: 10.3_

- [x] 25. Final checkpoint - Comprehensive testing and validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all 30 correctness properties are tested
  - Verify all requirements are covered
  - Verify error handling works for all scenarios
  - Verify security measures are in place

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples, edge cases, and error conditions
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- The implementation follows a bottom-up approach: infrastructure → services → integration
- Python is used for backend with FastAPI framework
- Property-based testing uses `hypothesis` library
- All property tests must be tagged with: `Feature: bharatsahayak, Property {number}: {property_title}`
