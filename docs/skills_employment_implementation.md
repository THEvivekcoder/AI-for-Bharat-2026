# Skills and Employment Service Implementation

## Overview

Successfully implemented the Skills and Employment Service for BharatSahayak, providing skill program matching and government job search functionality for rural users.

## Implementation Summary

### Task 10.1: Data Models ✅

Created database models and schemas:

**Models** (`app/models/skills.py`):
- `SkillProgram`: Skill development program information
  - Fields: name, provider, category, duration, cost, location, mode, eligibility, certification, placement support
- `JobPosting`: Government job posting information
  - Fields: title, department, description, qualifications, location, deadline, application URL

**Database Migration**:
- Created Alembic migration `1825c4aef2aa_add_skills_and_jobs_tables.py`
- Successfully applied migration to PostgreSQL database

**Schemas** (`app/schemas/skills.py`):
- `SkillProgramBase`, `SkillProgramCreate`, `SkillProgramResponse`
- `JobPostingBase`, `JobPostingCreate`, `JobPostingResponse`
- `SkillPreferences`, `SkillMatchRequest`
- `Qualifications`, `JobPreferences`, `JobSearchRequest`, `JobAlertsRequest`

### Task 10.2: Skills Matcher ✅

Implemented `SkillsMatcher` service (`app/services/skills_matcher.py`):

**Key Features**:
- `match_programs()`: Matches users with relevant skill programs based on:
  - Interests (40% weight)
  - Career goals (30% weight)
  - Current skills (20% weight)
  - Certification and placement support bonuses
  - Location convenience
  - Education level matching
- `_calculate_relevance_score()`: Sophisticated scoring algorithm with explanations
- `get_program_details()`: Retrieve individual program details
- `get_all_programs()`: List all programs with filters

**Scoring Algorithm**:
- Interest matching: 0.4 weight
- Career goals: 0.3 weight
- Skill building: 0.2 weight
- Certification bonus: 0.05
- Placement support bonus: 0.05
- Location and education bonuses

### Task 10.3: Job Matcher ✅

Implemented `JobMatcher` service (`app/services/job_matcher.py`):

**Key Features**:
- `search_jobs()`: Matches users with government jobs based on:
  - Education level (30% weight) - allows one level below requirement
  - Experience (25% weight)
  - Skills matching (20% weight)
  - Department preference (15% weight)
  - Location preference (10% weight)
  - Deadline urgency and recency bonuses
- `get_job_alerts()`: Find recent job postings (last N days)
- `_check_qualification_match()`: Validates user meets job requirements
- `_check_location_match()`: Flexible location matching

**Education Level Hierarchy**:
- below_10th → 10th → 12th → diploma → graduate → postgraduate → doctorate
- Allows matching if user is within one level of requirement

### Task 10.4: API Endpoints ✅

Created REST API endpoints (`app/api/skills.py`):

**Skill Program Endpoints**:
- `GET /api/skills`: List all skill programs with filters
  - Query params: category, state, district, mode, limit, offset
- `POST /api/skills/match`: Get personalized program recommendations
  - Returns programs with relevance scores and match explanations
- `GET /api/skills/{program_id}`: Get program details

**Job Posting Endpoints**:
- `GET /api/jobs`: List all job postings with filters
  - Query params: title, department, state, limit, offset
- `POST /api/jobs/search`: Search jobs with qualification matching
  - Returns jobs with match scores and explanations
- `POST /api/jobs/alerts`: Get recent job postings matching user profile
  - Configurable days_back parameter (default 30 days)
- `GET /api/jobs/{job_id}`: Get job details

**Integration**:
- Registered router in `app/main.py`
- Added models to `app/models/__init__.py`
- All endpoints follow existing API patterns

## Testing

### Service Testing

Created `scripts/test_skills_service.py`:
- Tests skills matcher with various user profiles
- Tests job matcher with different qualifications
- Tests job alerts functionality
- All tests passing ✅

**Test Results**:
- Skills matching: 4 programs created, matching works correctly
- Job matching: 4 jobs created, scoring algorithm works as expected
- Job alerts: Correctly filters by date and matches qualifications

### API Testing

Created `scripts/test_skills_endpoints.py`:
- Tests all API endpoints
- Validates request/response formats
- Ready for integration testing

## Key Features

### Skills Matcher
1. **Intelligent Matching**: Multi-factor scoring based on interests, goals, and skills
2. **Flexible Filtering**: Location, cost, duration, mode filters
3. **Explanations**: Each match includes reason for recommendation
4. **Education Matching**: Validates eligibility criteria

### Job Matcher
1. **Qualification Validation**: Ensures users meet requirements (within one level)
2. **Smart Scoring**: Weights education, experience, skills, preferences
3. **Location Flexibility**: Handles multiple job locations
4. **Recency Awareness**: Prioritizes recent postings and urgent deadlines
5. **Job Alerts**: Finds new opportunities based on user profile

## Database Schema

### skill_programs Table
- program_id (UUID, PK)
- name, provider, category, description
- duration_weeks, cost
- state, district, mode
- eligibility_criteria (JSONB)
- certification, placement_support (Boolean)
- registration_url, contact
- created_at, updated_at

### job_postings Table
- job_id (UUID, PK)
- title, department, description
- qualifications (JSONB)
- location (JSONB)
- application_deadline, application_url
- posted_date
- created_at, updated_at

## API Routes Summary

Total new routes: 7

1. GET /api/skills - List programs
2. POST /api/skills/match - Match programs
3. GET /api/skills/{program_id} - Get program
4. GET /api/jobs - List jobs
5. POST /api/jobs/search - Search jobs
6. POST /api/jobs/alerts - Get alerts
7. GET /api/jobs/{job_id} - Get job

## Requirements Validation

✅ **Requirement 4.1**: Skill program matching with relevance scoring
✅ **Requirement 4.3**: Job search with qualification matching

## Next Steps

1. Add unit tests for edge cases (Task 10.7 - optional)
2. Add property-based tests (Tasks 10.5, 10.6 - optional)
3. Seed database with real government programs and jobs (Task 23.1)
4. Integrate with external job posting APIs (Task 23.2)

## Files Created/Modified

### Created:
- `app/models/skills.py` - Data models
- `app/schemas/skills.py` - Pydantic schemas
- `app/services/skills_matcher.py` - Skills matching service
- `app/services/job_matcher.py` - Job matching service
- `app/api/skills.py` - API endpoints
- `alembic/versions/2026_02_27_1952-1825c4aef2aa_add_skills_and_jobs_tables.py` - Migration
- `scripts/test_skills_service.py` - Service tests
- `scripts/test_skills_endpoints.py` - API tests
- `docs/skills_employment_implementation.md` - This document

### Modified:
- `app/main.py` - Added skills router
- `app/models/__init__.py` - Added new models
- `app/api/farmer.py` - Fixed redis import

## Notes

- All services follow existing patterns from scheme and farmer services
- Scoring algorithms are tunable via weights
- Education level hierarchy supports Indian education system
- Location matching handles both single and multiple locations
- All endpoints include proper error handling
- Ready for integration with frontend PWA
