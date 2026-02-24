# Implementation Plan: BharatSahayak

## Overview

This implementation plan breaks down the BharatSahayak multilingual AI assistant into discrete, manageable coding tasks. The system will be built using Python with FastAPI for the backend, PostgreSQL for primary data storage, Redis for caching, and a Progressive Web App frontend. The implementation follows a modular architecture with clear separation between voice processing, AI/RAG engine, domain services, and data layers.

The plan prioritizes core functionality first, with testing integrated throughout to catch errors early. Each task builds incrementally on previous work, ensuring no orphaned code.

## Tasks

- [ ] 1. Set up project structure and core infrastructure
  - Create directory structure for backend (api, services, models, db, tests)
  - Set up FastAPI application with basic configuration
  - Configure PostgreSQL database connection with SQLAlchemy
  - Set up Redis connection for caching
  - Create requirements.txt with core dependencies (fastapi, sqlalchemy, redis, pydantic)
  - Set up pytest testing framework
  - Create .env.example for environment variables
  - _Requirements: 11.1, 11.2_

- [ ] 2. Implement database schema and models
  - [ ] 2.1 Create SQLAlchemy models for core entities
    - Implement User model with profile fields (phone, language, location, demographics)
    - Implement Scheme model with eligibility criteria as JSONB
    - Implement SchemeTranslation model for multilingual content
    - Implement Interaction and Outcome models for impact tracking
    - Implement SkillProgram, JobPosting, HealthFacility, MandiPrice models
    - Implement ConversationSession model for chat history
    - _Requirements: 8.1, 2.1, 4.1, 5.2, 3.3, 6.1_
  
  - [ ] 2.2 Create database migration scripts
    - Write Alembic migration for creating all tables
    - Add indexes for frequently queried fields (phone_number, location, category)
    - Add foreign key constraints
    - _Requirements: 8.1_
  
  - [ ]* 2.3 Write property test for profile data round-trip
    - **Property 20: Profile Data Round-Trip**
    - **Validates: Requirements 8.1**
    - Generate random user profiles, store in DB, retrieve, verify equivalence

- [ ] 3. Implement authentication and user management
  - [ ] 3.1 Create UserManager service
    - Implement user registration with phone number
    - Implement OTP generation and verification (mock for now)
    - Implement JWT token generation and validation
    - Implement profile CRUD operations
    - Implement user data deletion for GDPR compliance
    - _Requirements: 11.1, 11.3, 8.1_
  
  - [ ] 3.2 Create authentication endpoints
    - POST /api/auth/register - register new user
    - POST /api/auth/verify - verify OTP and get token
    - GET /api/user/profile - get user profile (authenticated)
    - PUT /api/user/profile - update profile (authenticated)
    - DELETE /api/user/data - delete user data (authenticated)
    - _Requirements: 11.1, 11.3_
  
  - [ ]* 3.3 Write unit tests for authentication flows
    - Test registration with valid/invalid phone numbers
    - Test OTP verification success and failure cases
    - Test token expiration
    - Test profile update edge cases
    - _Requirements: 11.1_

- [ ] 4. Implement Scheme Service
  - [ ] 4.1 Create SchemeRepository
    - Implement search_schemes with keyword and filter support
    - Implement get_scheme_by_id
    - Implement get_all_schemes with category filtering
    - Add caching layer using Redis for frequently accessed schemes
    - _Requirements: 2.1_
  
  - [ ] 4.2 Create EligibilityChecker
    - Implement check_eligibility logic for age, income, occupation, location, gender
    - Implement get_eligible_schemes to filter all schemes by user profile
    - Implement explain_eligibility to generate human-readable explanations
    - _Requirements: 2.3_
  
  - [ ] 4.3 Create scheme endpoints
    - GET /api/schemes - list schemes with filters
    - GET /api/schemes/{id} - get scheme details
    - POST /api/schemes/check-eligibility - check eligibility for one scheme
    - POST /api/schemes/eligible - get all eligible schemes for user
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ]* 4.4 Write property test for scheme search relevance
    - **Property 4: Scheme Search Relevance**
    - **Validates: Requirements 2.1**
    - Generate random schemes and queries, verify retrieved schemes match semantically
  
  - [ ]* 4.5 Write property test for complete information display
    - **Property 5: Complete Information Display**
    - **Validates: Requirements 2.2**
    - Generate random schemes, verify all required fields are non-null in output
  
  - [ ]* 4.6 Write property test for eligibility determination correctness
    - **Property 6: Eligibility Determination Correctness**
    - **Validates: Requirements 2.3**
    - Generate random user profiles and schemes, verify eligibility logic correctness

- [ ] 5. Checkpoint - Ensure authentication and scheme service tests pass
  - Run all tests for authentication and scheme service
  - Verify database migrations work correctly
  - Ask the user if questions arise

- [ ] 6. Implement Farmer Advisory Service
  - [ ] 6.1 Create CropAdvisor
    - Implement recommend_crops based on soil type, season, location, water availability
    - Implement get_crop_calendar for planting and harvest schedules
    - Use rule-based logic with crop database (JSON file initially)
    - _Requirements: 3.1, 3.4_
  
  - [ ] 6.2 Create FertilizerAdvisor
    - Implement recommend_fertilizer based on crop, soil data, growth stage
    - Return fertilizer type, quantity, timing, application method
    - _Requirements: 3.2_
  
  - [ ] 6.3 Create MandiPriceService
    - Implement get_current_price to query prices within radius
    - Implement get_price_trend for historical data
    - Add caching with Redis (TTL 24 hours)
    - Mock external API initially
    - _Requirements: 3.3, 3.5_
  
  - [ ] 6.4 Create farmer advisory endpoints
    - POST /api/farmer/crop-advice - get crop recommendations
    - POST /api/farmer/fertilizer-advice - get fertilizer guidance
    - GET /api/farmer/market-price - get mandi prices
    - GET /api/farmer/crop-calendar - get crop calendar
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 6.5 Write property test for crop recommendation generation
    - **Property 7: Crop Recommendation Generation**
    - **Validates: Requirements 3.1**
    - Generate random farm profiles, verify recommendations have all required fields
  
  - [ ]* 6.6 Write property test for fertilizer guidance completeness
    - **Property 8: Fertilizer Guidance Completeness**
    - **Validates: Requirements 3.2**
    - Generate random crop/soil combinations, verify guidance contains all fields
  
  - [ ]* 6.7 Write property test for mandi price radius constraint
    - **Property 9: Mandi Price Radius Constraint**
    - **Validates: Requirements 3.3**
    - Generate random locations and prices, verify all results within radius and sorted by distance
  
  - [ ]* 6.8 Write unit test for missing market price handling
    - **Property 30: Missing Market Price Handling**
    - **Validates: Requirements 3.5**
    - Test behavior when price data unavailable, verify error message and fallback

- [ ] 7. Implement Skills and Employment Service
  - [ ] 7.1 Create SkillsMatcher
    - Implement match_programs based on user education, skills, interests, location
    - Implement get_program_details
    - Use scoring algorithm to rank programs by relevance
    - _Requirements: 4.1, 4.2_
  
  - [ ] 7.2 Create JobMatcher
    - Implement search_jobs with qualification and location filtering
    - Implement get_job_alerts for personalized job notifications
    - _Requirements: 4.3, 4.4_
  
  - [ ] 7.3 Create skills and employment endpoints
    - GET /api/skills - list skill programs
    - POST /api/skills/match - get personalized recommendations
    - GET /api/jobs - search government jobs
    - POST /api/jobs/alerts - get job alerts
    - _Requirements: 4.1, 4.3_
  
  - [ ]* 7.4 Write property test for skill program matching relevance
    - **Property 10: Skill Program Matching Relevance**
    - **Validates: Requirements 4.1**
    - Generate random user profiles and programs, verify matches are relevant
  
  - [ ]* 7.5 Write property test for job qualification matching
    - **Property 11: Job Search Qualification Matching**
    - **Validates: Requirements 4.3**
    - Generate random qualifications and jobs, verify returned jobs match criteria

- [ ] 8. Implement Health Advisory Service
  - [ ] 8.1 Create HealthAdvisor
    - Implement analyze_symptoms with urgency level determination
    - Implement find_facilities with radius search and distance calculation
    - Use symptom database (JSON file) with rule-based logic
    - Always include disclaimer in health guidance
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [ ] 8.2 Create health advisory endpoints
    - POST /api/health/check - submit symptoms, receive guidance
    - GET /api/health/facilities - find nearby health facilities
    - GET /api/health/schemes - get health insurance schemes
    - _Requirements: 5.1, 5.2, 5.4_
  
  - [ ]* 8.3 Write property test for health guidance generation
    - **Property 12: Health Guidance Generation**
    - **Validates: Requirements 5.1**
    - Generate random symptom lists, verify guidance has all required fields
  
  - [ ]* 8.4 Write property test for health facility distance accuracy
    - **Property 13: Health Facility Distance Accuracy**
    - **Validates: Requirements 5.2**
    - Generate random locations and facilities, verify distance calculations and sorting
  
  - [ ]* 8.5 Write property test for health disclaimer presence
    - **Property 14: Health Disclaimer Presence**
    - **Validates: Requirements 5.3**
    - Generate random health guidance, verify disclaimer always present
  
  - [ ]* 8.6 Write unit test for emergency symptom detection
    - **Property 29: Emergency Symptom Detection**
    - **Validates: Requirements 5.5**
    - Test specific emergency symptoms, verify urgency level set to "emergency"

- [ ] 9. Checkpoint - Ensure domain services tests pass
  - Run all tests for farmer, skills, and health services
  - Verify API endpoints return correct data structures
  - Ask the user if questions arise

- [ ] 10. Implement RAG Engine and Conversation Management
  - [ ] 10.1 Set up vector database
    - Choose and configure vector DB (Pinecone, Weaviate, or ChromaDB)
    - Create document schema with metadata (source, category, language)
    - Implement document ingestion pipeline
    - _Requirements: 6.2_
  
  - [ ] 10.2 Create RAGEngine
    - Implement query method with embedding generation
    - Implement document retrieval with semantic search (top-k)
    - Implement prompt construction with retrieved context
    - Integrate with LLM API (OpenAI or local model)
    - Implement source prioritization for official government sources
    - _Requirements: 6.1, 6.2, 6.5_
  
  - [ ] 10.3 Create ConversationManager
    - Implement create_session
    - Implement get_context to retrieve conversation history
    - Implement add_turn to update session with new messages
    - Store sessions in Redis with TTL (1 hour)
    - _Requirements: 6.1_
  
  - [ ] 10.4 Create RAG and conversation endpoints
    - POST /api/ask - submit query, receive AI response
    - POST /api/session/create - create conversation session
    - DELETE /api/session/{session_id} - clear session
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [ ]* 10.5 Write property test for conversation context preservation
    - **Property 15: Conversation Context Preservation**
    - **Validates: Requirements 6.1**
    - Generate random conversation histories, verify context maintained across turns
  
  - [ ]* 10.6 Write property test for semantic search relevance
    - **Property 16: Semantic Search Relevance**
    - **Validates: Requirements 6.2**
    - Generate random queries and documents, verify similarity scores above threshold
  
  - [ ]* 10.7 Write property test for official source prioritization
    - **Property 17: Official Source Prioritization**
    - **Validates: Requirements 6.5**
    - Generate mixed sources, verify official sources ranked higher
  
  - [ ]* 10.8 Write unit test for out-of-scope query handling
    - **Property 31: Out-of-Scope Query Handling**
    - **Validates: Requirements 6.4**
    - Test queries outside domain, verify appropriate limitation message

- [ ] 11. Implement Voice Interface Module
  - [ ] 11.1 Create SpeechToTextEngine
    - Integrate with STT service (Google Speech-to-Text, Whisper, or Bhashini)
    - Implement transcribe method with language detection
    - Implement preprocess_audio for noise reduction
    - Support Hindi and major regional languages
    - _Requirements: 1.1, 1.3, 1.4_
  
  - [ ] 11.2 Create TextToSpeechEngine
    - Integrate with TTS service (Google TTS, Azure TTS, or Bhashini)
    - Implement synthesize method for multiple languages
    - Support natural-sounding voices for Hindi and regional languages
    - _Requirements: 1.2_
  
  - [ ] 11.3 Create voice interface endpoints
    - POST /api/voice-to-text - upload audio, receive transcription
    - POST /api/text-to-voice - send text, receive audio
    - GET /api/languages - list supported languages
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 11.4 Write property test for voice-to-text transcription accuracy
    - **Property 1: Voice-to-Text Transcription Accuracy**
    - **Validates: Requirements 1.1**
    - Generate audio samples, verify transcription accuracy >= 85%
  
  - [ ]* 11.5 Write property test for text-to-speech audio generation
    - **Property 2: Text-to-Speech Audio Generation**
    - **Validates: Requirements 1.2**
    - Generate random text, verify valid audio output produced
  
  - [ ]* 11.6 Write property test for language detection accuracy
    - **Property 3: Language Detection Accuracy**
    - **Validates: Requirements 1.3**
    - Generate audio in different languages, verify correct language detected

- [ ] 12. Implement Language Processing Module
  - [ ] 12.1 Create LanguageProcessor
    - Integrate translation service (Google Translate or IndicTrans)
    - Implement translate method for supported language pairs
    - Implement detect_language for text
    - Implement romanize and transliterate for Indic scripts
    - _Requirements: 1.1, 2.2, 4.2, 5.1_
  
  - [ ] 12.2 Create language processing endpoints
    - POST /api/translate - translate text between languages
    - POST /api/detect-language - detect language of text
    - POST /api/transliterate - convert between scripts
    - _Requirements: 1.1_
  
  - [ ]* 12.3 Write unit tests for translation and transliteration
    - Test translation accuracy for common phrases
    - Test script conversion edge cases
    - Test language detection with mixed content

- [ ] 13. Implement Impact Tracking Service
  - [ ] 13.1 Create ImpactTracker
    - Implement record_interaction to log user events
    - Implement record_outcome to log successful actions
    - Implement get_metrics with aggregation by region, language, category
    - Implement generate_report for impact reporting
    - Ensure PII anonymization in all analytics
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 13.2 Create impact tracking endpoints
    - POST /api/impact/event - record interaction or outcome
    - GET /api/impact - get impact metrics with filters
    - GET /api/impact/report - generate impact report
    - _Requirements: 9.1, 9.2_
  
  - [ ]* 13.3 Write property test for interaction event recording
    - **Property 23: Interaction Event Recording**
    - **Validates: Requirements 9.1, 9.3**
    - Generate random interactions, verify all required fields recorded
  
  - [ ]* 13.4 Write property test for impact metrics aggregation
    - **Property 24: Impact Metrics Aggregation**
    - **Validates: Requirements 9.2**
    - Generate random events, verify aggregations sum correctly
  
  - [ ]* 13.5 Write property test for analytics data anonymization
    - **Property 25: Analytics Data Anonymization**
    - **Validates: Requirements 9.4**
    - Generate analytics queries, verify no PII in results

- [ ] 14. Implement Offline Cache Manager
  - [ ] 14.1 Create SQLite schema for offline cache
    - Create cached_schemes, cached_content, pending_sync, user_preferences tables
    - Implement schema migration for SQLite
    - _Requirements: 7.1, 7.3_
  
  - [ ] 14.2 Create CacheManager
    - Implement cache_content with priority-based storage
    - Implement get_cached_content for offline retrieval
    - Implement sync_with_server for bidirectional sync
    - Implement invalidate_cache for stale data removal
    - _Requirements: 7.1, 7.3, 7.4_
  
  - [ ] 14.3 Create cache management endpoints
    - POST /api/cache/sync - trigger sync with server
    - GET /api/cache/status - get cache status and last sync time
    - _Requirements: 7.4_
  
  - [ ]* 14.4 Write property test for offline cache priority
    - **Property 19: Offline Cache Priority**
    - **Validates: Requirements 7.3**
    - Generate random content with priorities, verify high-priority cached first

- [ ] 15. Implement personalization and recommendations
  - [ ] 15.1 Create RecommendationEngine
    - Implement personalized scheme filtering based on user profile
    - Implement personalized job and skill program ranking
    - Implement recommendation explanation generation
    - Track user interactions to improve recommendations
    - _Requirements: 8.2, 8.3, 8.4_
  
  - [ ] 15.2 Integrate personalization into existing endpoints
    - Update /api/schemes/eligible to use personalization
    - Update /api/skills/match to use personalization
    - Update /api/jobs/alerts to use personalization
    - Add explanation field to all recommendation responses
    - _Requirements: 8.2, 8.4_
  
  - [ ]* 15.3 Write property test for personalized recommendation filtering
    - **Property 21: Personalized Recommendation Filtering**
    - **Validates: Requirements 8.2**
    - Generate different user profiles, verify recommendations differ appropriately
  
  - [ ]* 15.4 Write property test for recommendation explanation presence
    - **Property 22: Recommendation Explanation Presence**
    - **Validates: Requirements 8.4**
    - Generate random recommendations, verify explanation field always present

- [ ] 16. Checkpoint - Ensure AI and personalization features work
  - Run all tests for RAG engine, voice interface, and personalization
  - Test end-to-end voice query flow
  - Verify conversation context maintained across multiple turns
  - Ask the user if questions arise

- [ ] 17. Implement data security and privacy features
  - [ ] 17.1 Add encryption for sensitive data
    - Implement AES-256 encryption for PII fields in database
    - Implement TLS 1.3 for all API endpoints
    - Add encryption key management
    - _Requirements: 11.1, 11.2_
  
  - [ ] 17.2 Implement role-based access control
    - Create admin role for impact tracking and reports
    - Create user role for standard access
    - Add middleware for authorization checks
    - Implement audit logging for data access
    - _Requirements: 11.4_
  
  - [ ] 17.3 Add rate limiting and security middleware
    - Implement rate limiting per user (100 requests/hour)
    - Add CORS configuration
    - Add request validation and sanitization
    - Add security headers (HSTS, CSP, X-Frame-Options)
    - _Requirements: 11.1_
  
  - [ ]* 17.4 Write unit tests for security features
    - Test encryption/decryption round-trip
    - Test rate limiting enforcement
    - Test authorization checks
    - Test audit logging

- [ ] 18. Implement content freshness and accuracy tracking
  - [ ] 18.1 Add data freshness tracking
    - Add last_updated and last_verified timestamps to all content models
    - Create background job to update scheme data from government APIs
    - Create background job to update mandi prices daily
    - Implement data verification workflow
    - _Requirements: 2.5, 3.5, 12.1, 12.2_
  
  - [ ] 18.2 Add uncertainty indicators
    - Add source attribution to all responses
    - Add confidence scores where applicable
    - Add "last updated" timestamps to time-sensitive data
    - Implement flagging system for user-reported incorrect information
    - _Requirements: 12.3, 12.4, 12.5_
  
  - [ ]* 18.3 Write property test for scheme data freshness tracking
    - **Property 26: Scheme Data Freshness Tracking**
    - **Validates: Requirements 12.1**
    - Generate random schemes, verify last_updated timestamp present
  
  - [ ]* 18.4 Write property test for unverified information indicators
    - **Property 27: Unverified Information Indicators**
    - **Validates: Requirements 12.3**
    - Generate unverified content, verify uncertainty indicator present
  
  - [ ]* 18.5 Write property test for time-sensitive data timestamps
    - **Property 28: Time-Sensitive Data Timestamps**
    - **Validates: Requirements 12.5**
    - Generate time-sensitive responses, verify timestamps included

- [ ] 19. Implement bandwidth optimization
  - [ ] 19.1 Add response compression
    - Implement gzip compression for all API responses
    - Add response size monitoring
    - Implement pagination for large result sets
    - _Requirements: 7.2_
  
  - [ ] 19.2 Optimize data transfer
    - Implement field selection (return only requested fields)
    - Minimize JSON payload sizes
    - Use efficient serialization
    - _Requirements: 7.2_
  
  - [ ]* 19.3 Write property test for bandwidth constraint compliance
    - **Property 18: Bandwidth Constraint Compliance**
    - **Validates: Requirements 7.2**
    - Generate random API responses, verify compressed size < 100KB

- [ ] 20. Create Progressive Web App frontend
  - [ ] 20.1 Set up PWA structure
    - Create React/Vue.js application with PWA template
    - Configure service worker for offline support
    - Implement app manifest for installability
    - Set up build pipeline with optimization for low-end devices
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 20.2 Implement voice interface UI
    - Create voice input component with recording controls
    - Create audio playback component for TTS responses
    - Add visual feedback for voice processing
    - Implement language selector
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 20.3 Implement chat interface
    - Create conversation UI with message history
    - Implement text input fallback
    - Add typing indicators and loading states
    - Implement error handling and retry UI
    - _Requirements: 6.1_
  
  - [ ] 20.4 Implement service-specific UIs
    - Create scheme search and display UI
    - Create farmer advisory UI with crop and price lookup
    - Create skills and jobs search UI
    - Create health check UI with symptom input
    - _Requirements: 2.1, 3.1, 4.1, 5.1_
  
  - [ ] 20.5 Implement offline functionality
    - Configure service worker to cache API responses
    - Implement offline indicator
    - Implement sync queue for offline actions
    - Add offline-first data access patterns
    - _Requirements: 7.1, 7.4_
  
  - [ ]* 20.6 Write integration tests for PWA
    - Test voice recording and playback
    - Test offline mode functionality
    - Test service worker caching
    - Test on low-end device simulators

- [ ] 21. Implement data seeding and initial content
  - [ ] 21.1 Create seed data scripts
    - Create script to seed government schemes (100+ schemes)
    - Create script to seed skill programs (50+ programs)
    - Create script to seed health facilities (sample data)
    - Create script to seed crop and fertilizer data
    - _Requirements: 2.1, 3.1, 4.1, 5.2_
  
  - [ ] 21.2 Ingest documents into vector database
    - Prepare government scheme documents for RAG
    - Prepare agricultural guidance documents
    - Prepare health information documents
    - Run ingestion pipeline to populate vector DB
    - _Requirements: 6.2_

- [ ] 22. Final integration and end-to-end testing
  - [ ] 22.1 Test complete user journeys
    - Test: User registration → Profile creation → Scheme discovery → Eligibility check
    - Test: Voice query → STT → RAG → Response → TTS
    - Test: Farmer query → Crop advice → Market prices
    - Test: Health symptom check → Facility lookup
    - Test: Offline mode → Cache access → Sync on reconnection
    - _Requirements: All_
  
  - [ ] 22.2 Performance and load testing
    - Test with 100+ concurrent users
    - Verify response times < 3 seconds (95th percentile)
    - Test on low-end devices (1GB RAM)
    - Test with 2G network simulation
    - _Requirements: 10.3, 7.2_
  
  - [ ]* 22.3 Write integration tests for critical flows
    - Test authentication flow end-to-end
    - Test voice query flow end-to-end
    - Test personalized recommendations flow
    - Test offline sync flow

- [ ] 23. Documentation and deployment preparation
  - [ ] 23.1 Create API documentation
    - Generate OpenAPI/Swagger documentation
    - Document all endpoints with examples
    - Document authentication requirements
    - Document error responses
  
  - [ ] 23.2 Create deployment configuration
    - Create Dockerfile for backend
    - Create docker-compose for local development
    - Create Kubernetes manifests for production (optional)
    - Document environment variables and configuration
    - _Requirements: 10.1_
  
  - [ ] 23.3 Create operational runbooks
    - Document database backup and restore procedures
    - Document monitoring and alerting setup
    - Document incident response procedures
    - Document data update procedures

- [ ] 24. Final checkpoint - Complete system verification
  - Run full test suite (unit + property + integration tests)
  - Verify all API endpoints functional
  - Verify PWA installable and works offline
  - Verify voice interface works in multiple languages
  - Verify data security and privacy features active
  - Ask the user if questions arise before considering implementation complete

## Notes

- Tasks marked with `*` are optional testing tasks that can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property-based tests use hypothesis library with minimum 100 iterations
- Integration tests verify end-to-end flows across multiple components
- The implementation prioritizes core functionality (schemes, farmer advisory, voice) before advanced features (personalization, offline sync)
- External service integrations (STT, TTS, translation) can use mock implementations initially and be replaced with real services later
- Database seeding should use real government data sources where available
- Security features (encryption, rate limiting, RBAC) are integrated throughout rather than added at the end
