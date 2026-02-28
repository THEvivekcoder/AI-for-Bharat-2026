# Personalization and Recommendation Engine Implementation

## Overview

Implemented a comprehensive personalization and recommendation engine for BharatSahayak that provides personalized relevance scoring and explanations for schemes, jobs, and skill programs based on user profiles.

## Implementation Summary

### Task 16.1: Create Recommendation Scoring Algorithms ✓

Created `app/services/personalization.py` with the `PersonalizationEngine` class that implements:

**Scheme Scoring Algorithm:**
- Occupation match (25% weight)
- Location match (20% weight)
- Income match (20% weight)
- Age match (15% weight)
- Education match (10% weight)
- Category preference (10% weight)

**Job Scoring Algorithm:**
- Education match (30% weight)
- Experience match (25% weight)
- Skills match (20% weight)
- Location match (15% weight)
- Department preference (10% weight)

**Skill Program Scoring Algorithm:**
- Interest match (35% weight)
- Career goal match (25% weight)
- Skill building (20% weight)
- Location match (10% weight)
- Education match (10% weight)

### Task 16.2: Integrate Personalization into Services ✓

**Scheme Service Integration:**
- Updated `app/api/schemes.py` to add personalized ranking to `/api/schemes/eligible` endpoint
- Added `personalized` query parameter (default: True) to enable/disable personalization
- Schemes are now ranked by relevance score with explanations
- Updated `EligibilityResult` schema to include `relevance_score` and `explanation` fields

**Skills Service Integration:**
- Updated `app/services/skills_matcher.py` to use `PersonalizationEngine`
- Skill program matching now uses personalized scoring
- Maintains backward compatibility with existing relevance checks
- Explanations describe why programs match user interests, goals, and skills

**Job Service Integration:**
- Updated `app/services/job_matcher.py` to use `PersonalizationEngine`
- Job matching now uses personalized scoring
- Explanations describe qualification matches and location preferences
- Both `search_jobs` and `get_job_alerts` methods use personalization

### Task 16.3: Implement Recommendation Explanations ✓

**Explanation Generation:**
- Each scoring method returns a tuple of (score, explanation)
- Explanations are human-readable and describe why items are recommended
- Added `generate_detailed_explanation()` method for enhanced explanations
- Explanations include:
  - Relevance level (Highly recommended, Good match, Moderate match, May be relevant)
  - Specific matching criteria (occupation, education, interests, etc.)
  - Profile-specific context (location, experience, skills)

**Example Explanations:**
- Scheme: "Recommended because it designed for farmers, available nationwide, matches your income level"
- Job: "Recommended because matches your education level, you meet the 2 years experience requirement, you have 1 of 2 required skills"
- Skill Program: "Recommended because it matches your interests, aligns with your career goals, available online"

## Key Features

1. **Multi-dimensional Scoring:** Considers multiple user profile attributes with configurable weights
2. **Transparent Explanations:** Every recommendation includes a clear explanation of why it was recommended
3. **Flexible Integration:** Can be used standalone or integrated into existing services
4. **Ranking Support:** Can rank lists of items by personalized relevance
5. **Type-specific Logic:** Different scoring algorithms optimized for schemes, jobs, and skill programs

## API Changes

### Schemes API
- `/api/schemes/eligible` now accepts `personalized=true/false` query parameter
- Response includes `relevance_score` and `explanation` in `eligibility` field

### Skills API
- `/api/skills/match` returns programs with `relevance_score` and `match_reason`
- Explanations describe interest, goal, and skill matches

### Jobs API
- `/api/jobs/search` returns jobs with `match_score` and `match_reason`
- `/api/jobs/alerts` includes personalized scoring
- Explanations describe qualification and preference matches

## Testing

Created `scripts/test_personalization.py` with comprehensive tests:
- ✓ Scheme relevance scoring
- ✓ Job relevance scoring
- ✓ Skill program relevance scoring
- ✓ Multi-item ranking
- ✓ Detailed explanation generation

All tests pass successfully.

## Requirements Validation

**Requirement 8.2: Personalized Recommendations**
- ✓ User profile data used to filter and rank schemes, jobs, and programs
- ✓ Different profiles produce different recommendations
- ✓ Scoring considers occupation, location, education, income, interests, skills

**Requirement 8.4: Recommendation Explanations**
- ✓ Every recommendation includes explanation field
- ✓ Explanations describe why items are recommended based on user profile
- ✓ Explanations are human-readable and specific to matching criteria

## Files Created/Modified

**Created:**
- `app/services/personalization.py` - PersonalizationEngine implementation
- `scripts/test_personalization.py` - Test suite
- `docs/personalization_implementation.md` - This document

**Modified:**
- `app/api/schemes.py` - Added personalized ranking to eligible schemes endpoint
- `app/services/skills_matcher.py` - Integrated PersonalizationEngine
- `app/services/job_matcher.py` - Integrated PersonalizationEngine
- `app/schemas/scheme.py` - Added relevance_score field to EligibilityResult

## Usage Examples

### Scheme Personalization
```python
from app.services.personalization import PersonalizationEngine

engine = PersonalizationEngine()

scheme = {
    "name": "PM-KISAN",
    "category": "agriculture",
    "eligibility_criteria": {"occupation": ["farmer"]}
}

user_profile = {
    "occupation": "farmer",
    "state": "Punjab"
}

score, explanation = engine.score_scheme_relevance(scheme, user_profile)
# score: 0.81
# explanation: "Recommended because it designed for farmers, available nationwide"
```

### Job Personalization
```python
job = {
    "title": "Junior Engineer",
    "qualifications": {
        "education_level": "graduate",
        "experience_years": 2
    }
}

user_profile = {
    "education_level": "graduate",
    "experience_years": 3
}

score, explanation = engine.score_job_relevance(job, user_profile)
# score: 0.80
# explanation: "Recommended because matches your education level, you meet the experience requirement"
```

### Ranking Multiple Items
```python
schemes = [scheme1, scheme2, scheme3]
ranked = engine.rank_recommendations(schemes, user_profile, "scheme")
# Returns list of (item, score, explanation) tuples sorted by score
```

## Next Steps

The personalization engine is now fully integrated and ready for use. Future enhancements could include:

1. **Learning from User Behavior:** Track which recommendations users act on to improve scoring
2. **A/B Testing:** Test different weight configurations to optimize relevance
3. **Collaborative Filtering:** Use patterns from similar users to improve recommendations
4. **Temporal Factors:** Consider time-sensitive factors like application deadlines
5. **Negative Signals:** Learn from items users explicitly reject

## Conclusion

Task 16 is complete. The personalization and recommendation engine successfully provides:
- Personalized relevance scoring for schemes, jobs, and skill programs
- Integration with existing services (Scheme, Skills, Job)
- Clear, human-readable explanations for all recommendations
- Validation through comprehensive testing

All subtasks completed successfully with no errors.
