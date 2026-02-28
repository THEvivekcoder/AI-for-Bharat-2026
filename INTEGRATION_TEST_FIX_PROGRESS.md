# Integration Test Fix Progress

## Summary
Systematically fixing integration test failures using "stop at first failure" approach (`pytest -x`).

## Fixes Applied

### 1. ErrorResponse Schema Mismatch ✅
**Problem**: `ErrorResponse` Pydantic model expected field `error` but middleware was using `error_code`

**Root Cause**: 
- Schema in `app/schemas/errors.py` defines: `error: str`
- Middleware in `app/middleware/error_handling.py` was creating: `error_code=...`

**Solution**: 
- Changed all `error_code` to `error` in error_handling.py
- Removed unused fields (`details`, `suggestions`) that don't exist in base ErrorResponse

**Files Modified**:
- `app/middleware/error_handling.py` (7 occurrences fixed)

### 2. DateTime JSON Serialization ✅
**Problem**: `TypeError: Object of type datetime is not JSON serializable`

**Root Cause**: 
- ErrorResponse has `timestamp: datetime` field
- Using `.dict()` doesn't convert datetime to JSON-serializable format

**Solution**: 
- Replaced all `.dict()` calls with `.model_dump(mode='json')` 
- This properly serializes datetime objects to ISO format strings

**Files Modified**:
- `app/middleware/error_handling.py` (7 occurrences fixed)

### 3. Integration Orchestrator Test Mock Path ✅
**Problem**: Test was getting 500 error because RAGEngine initialization failed (OpenAI not installed)

**Root Cause**: 
- Test was mocking `app.services.voice_interface.get_stt_engine` and `RAGEngine.query`
- But error occurred in `get_orchestrator` dependency which creates RAGEngine in `__init__`
- Mock needs to be at the dependency level, not the service level

**Solution**: 
- Changed mock from individual services to `app.api.integrated.get_orchestrator`
- Mock returns orchestrator with `process_voice_query` as AsyncMock
- Added `AsyncMock` import to test file

**Files Modified**:
- `.kiro/specs/bharatsahayak/tests/test_integration_e2e.py`

## Current Status
- Fixed: 3 issues
- Test still failing with 500 error (need to investigate further)
- Next: Check if mock is being applied correctly

## Test Command
```bash
pytest -x --ignore=.kiro/specs/bharatsahayak/tests/test_integration_pwa.py -v
```

## Pattern Identified
1. **Field name mismatches** between schemas and usage
2. **JSON serialization** issues with complex types (datetime, UUID)
3. **Mock paths** must be where function is USED, not DEFINED
4. **Dependency mocking** for FastAPI endpoints requires mocking the dependency function

## Next Steps
1. Verify the orchestrator mock is being applied correctly
2. Check if there are other initialization errors
3. Continue with next failing test using same systematic approach
