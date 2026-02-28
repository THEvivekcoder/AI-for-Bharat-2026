# Impact Tracker Data Models Implementation

## Overview

This document describes the implementation of the Impact Tracker data models for the BharatSahayak system. The Impact Tracker is responsible for recording user interactions and outcomes to measure social impact and system effectiveness.

## Implementation Date

February 27, 2026

## Components Implemented

### 1. Database Models (`app/models/impact.py`)

#### InteractionEvent Model
- **Table**: `interactions`
- **Purpose**: Records user interaction events for analytics
- **Fields**:
  - `interaction_id` (UUID): Primary key
  - `user_id` (UUID): Foreign key to users table (nullable for anonymous tracking)
  - `event_type` (String): Type of interaction (e.g., query_submitted, scheme_accessed)
  - `event_data` (JSONB): Additional event metadata
  - `language` (String): Language used during interaction
  - `timestamp` (DateTime): When the event occurred

#### OutcomeEvent Model
- **Table**: `outcomes`
- **Purpose**: Records successful outcomes for impact measurement
- **Fields**:
  - `outcome_id` (UUID): Primary key
  - `user_id` (UUID): Foreign key to users table (nullable for anonymous tracking)
  - `outcome_type` (String): Type of outcome (e.g., scheme_applied, job_applied)
  - `outcome_data` (JSONB): Additional outcome metadata
  - `timestamp` (DateTime): When the outcome occurred

### 2. Pydantic Schemas (`app/schemas/impact.py`)

#### Request Schemas
- `InteractionEventCreate`: For creating interaction events
- `OutcomeEventCreate`: For creating outcome events
- `MetricFilters`: For filtering impact metrics queries
- `DateRange`: For specifying date ranges in reports

#### Response Schemas
- `InteractionEventResponse`: Interaction event details
- `OutcomeEventResponse`: Outcome event details
- `ImpactMetrics`: Aggregated impact metrics
- `ImpactReport`: Comprehensive impact report
- `EventRecordResponse`: Confirmation after recording events

#### Enums
- `InteractionEventType`: Valid interaction event types
  - QUERY_SUBMITTED
  - SCHEME_ACCESSED
  - JOB_DISCOVERED
  - FACILITY_LOCATED
  - VOICE_INTERACTION
  - LANGUAGE_USED
  - CROP_ADVICE_REQUESTED
  - FERTILIZER_ADVICE_REQUESTED
  - MARKET_PRICE_CHECKED
  - SKILL_PROGRAM_VIEWED
  - HEALTH_CHECK_PERFORMED

- `OutcomeEventType`: Valid outcome event types
  - SCHEME_APPLIED
  - JOB_APPLIED
  - FACILITY_VISITED
  - SKILL_ENROLLED
  - RECOMMENDATION_FOLLOWED
  - CROP_PLANTED
  - FERTILIZER_PURCHASED

- `ReportType`: Valid report types
  - DAILY
  - WEEKLY
  - MONTHLY
  - QUARTERLY
  - CUSTOM

### 3. Database Migration

**Migration File**: `alembic/versions/2026_02_27_2111-960621aea9ec_add_impact_tracking_tables.py`

**Tables Created**:
1. `interactions` table with indexes on:
   - user_id
   - event_type
   - language
   - timestamp
   - (user_id, timestamp) composite
   - (event_type, timestamp) composite

2. `outcomes` table with indexes on:
   - user_id
   - outcome_type
   - timestamp
   - (user_id, timestamp) composite
   - (outcome_type, timestamp) composite

**Indexes**: Optimized for common query patterns:
- Filtering by user
- Filtering by event/outcome type
- Time-based queries
- Aggregations by user and time
- Aggregations by type and time

## Key Design Decisions

### 1. Anonymous Tracking Support
- Both `user_id` fields are nullable to support anonymous tracking
- Foreign key constraint uses `SET NULL` on delete to preserve analytics data
- Allows tracking system usage without requiring user authentication

### 2. JSONB for Flexibility
- `event_data` and `outcome_data` use JSONB for flexible metadata storage
- Allows storing different data structures for different event types
- Enables querying within JSON data using PostgreSQL JSONB operators

### 3. Comprehensive Indexing
- Multiple indexes to support various query patterns
- Composite indexes for common filter combinations
- Optimized for both real-time recording and batch analytics queries

### 4. Privacy by Design
- User ID is optional (supports anonymous tracking)
- Foreign key with SET NULL preserves analytics while allowing user deletion
- Supports Requirements 9.4 (data anonymization)

## Testing

### Test Script: `scripts/test_impact_models.py`

**Tests Implemented**:
1. ✓ InteractionEvent creation and retrieval
2. ✓ OutcomeEvent creation and retrieval
3. ✓ Pydantic schema validation
4. ✓ Anonymous event tracking (NULL user_id)

**Test Results**: All tests passing

## Database Schema

```sql
-- Interactions table
CREATE TABLE interactions (
    interaction_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    language VARCHAR(10),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Outcomes table
CREATE TABLE outcomes (
    outcome_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    outcome_type VARCHAR(50) NOT NULL,
    outcome_data JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 9.1**: Record user interactions with event_type, event_data, and timestamp
- **Requirement 9.3**: Track successful outcomes with outcome_type and outcome_data
- **Requirement 9.4**: Support anonymous tracking for privacy (nullable user_id)

## Next Steps

The following tasks remain for the Impact Tracking Service:

1. **Task 14.2**: Implement Impact Tracker service class
   - `record_interaction()` function
   - `record_outcome()` function
   - `get_metrics()` function with aggregation
   - `generate_report()` function

2. **Task 14.3**: Create Impact Tracking API endpoints
   - POST /api/impact/event
   - GET /api/impact
   - GET /api/impact/report

3. **Task 14.4-14.7**: Write property-based and unit tests

## Files Created/Modified

### Created:
- `app/models/impact.py` - SQLAlchemy models
- `app/schemas/impact.py` - Pydantic schemas
- `alembic/versions/2026_02_27_2111-960621aea9ec_add_impact_tracking_tables.py` - Database migration
- `scripts/test_impact_models.py` - Test script
- `docs/impact_tracker_models_implementation.md` - This documentation

### Modified:
- `app/models/__init__.py` - Added impact model imports

## Usage Examples

### Creating an Interaction Event

```python
from app.models.impact import InteractionEvent
from datetime import datetime

event = InteractionEvent(
    user_id=user_id,  # or None for anonymous
    event_type="query_submitted",
    event_data={"query": "PM Kisan scheme", "service": "schemes"},
    language="hi",
    timestamp=datetime.utcnow()
)
db.add(event)
db.commit()
```

### Creating an Outcome Event

```python
from app.models.impact import OutcomeEvent

outcome = OutcomeEvent(
    user_id=user_id,  # or None for anonymous
    outcome_type="scheme_applied",
    outcome_data={
        "scheme_id": scheme_id,
        "scheme_name": "PM Kisan",
        "application_method": "online"
    },
    timestamp=datetime.utcnow()
)
db.add(outcome)
db.commit()
```

### Using Pydantic Schemas

```python
from app.schemas.impact import InteractionEventCreate, InteractionEventType

# Validate request data
event_data = InteractionEventCreate(
    user_id=str(user_id),
    event_type=InteractionEventType.QUERY_SUBMITTED,
    event_data={"query": "test"},
    language="hi"
)
```

## Performance Considerations

1. **Indexes**: Comprehensive indexing ensures fast queries for:
   - User activity tracking
   - Event type aggregations
   - Time-based analytics
   - Regional breakdowns

2. **JSONB**: PostgreSQL JSONB provides:
   - Efficient storage
   - Fast querying within JSON data
   - Flexibility for different event types

3. **Partitioning**: Consider table partitioning by timestamp for large-scale deployments

## Conclusion

Task 14.1 has been successfully completed. The Impact Tracker data models provide a solid foundation for recording user interactions and outcomes, enabling comprehensive social impact measurement and analytics for the BharatSahayak system.
