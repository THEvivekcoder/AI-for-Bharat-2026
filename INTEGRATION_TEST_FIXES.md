# Integration Test Fixes - In Progress

## Summary

Systematically fixing integration test failures using the "stop at first failure" approach.

## Fixes Applied

### 1. Voice-to-RAG Integration Test ✅
**File**: `.kiro/specs/bharatsahayak/tests/test_integration_e2e.py`
**Test**: `TestVoiceToRAGIntegration::test_voice_to_text_to_rag_flow`

**Problem**: Mock patch path was incorrect
- Used: `@patch('app.services.voice_interface.get_stt_engine')`
- Should be: `@patch('app.api.voice.get_stt_engine')`

**Root Cause**: The function is imported in `app/api/voice.py` from `app.services.voice_interface`, so the patch must target where it's used, not where it's defined.

**Fix**:
```python
@patch('app.api.voice.get_stt_engine')  # Correct path
@patch('app.services.rag_engine.RAGEngine.query')
def test_voice_to_text_to_rag_flow(self, mock_rag_query, mock_stt, client, auth_headers, test_db):
```

**Also Added**: `test_db` fixture parameter (was missing)

### 2. RAG-to-Scheme Service Test ✅
**File**: `.kiro/specs/bharatsahayak/tests/test_integration_e2e.py`
**Test**: `TestRAGToDomainServicesIntegration::test_rag_to_scheme_service_flow`

**Problem 1**: Used `db` instead of `test_db`
- Found 30+ occurrences of `db.add()`, `db.commit()`, `db.query()`, `db.flush()`
- All needed to be replaced with `test_db.*`

**Fix 1**: Global replacement
```python
# Replaced all occurrences
db.add() → test_db.add()
db.commit() → test_db.commit()
db.query() → test_db.query()
db.flush() → test_db.flush()
```

**Problem 2**: SQLite doesn't support list/dict types directly
- Error: `sqlite3.ProgrammingError: Error binding parameter 5: type 'list' is not supported`
- JSONB fields (benefits, eligibility_criteria, etc.) were being stored as Python objects

**Fix 2**: Added SQLiteJSONB type converter in `conftest.py`
```python
class SQLiteJSONB(TypeDecorator):
    """Platform-independent JSONB type for SQLite"""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return json.loads(value)
```

## Pattern Identified

Integration tests have systematic issues:

1. **Missing `test_db` fixture**: Many tests don't include it in parameters
2. **Wrong variable name**: Using `db` instead of `test_db`
3. **Wrong mock paths**: Patching where function is defined, not where it's used
4. **SQLite compatibility**: Need JSON serialization for JSONB fields

## Files Modified

1. `.kiro/specs/bharatsahayak/tests/test_integration_e2e.py`:
   - Fixed mock patch path for voice STT
   - Added `test_db` fixture parameter
   - Replaced all `db.*` with `test_db.*` (30+ occurrences)

2. `conftest.py`:
   - Added `SQLiteJSONB` type converter
   - Updated `before_create` event to use `SQLiteJSONB()` instead of `Text()`
   - Added `import json`

## Test Results

**Before**:
```
166 failed, 696 passed, 15 errors
```

**After (so far)**:
```
2 tests fixed and passing
```

## Next Steps

Continue with `-x` (stop at first failure) approach:
1. Run: `pytest -x --ignore=test_integration_pwa.py`
2. Fix the first failure
3. Repeat

This systematic approach ensures:
- Each fix is verified immediately
- No cascading failures
- Clear understanding of each issue
- Incremental progress

## Status

🔄 **IN PROGRESS**

Fixing integration tests one at a time using senior engineer methodology.
