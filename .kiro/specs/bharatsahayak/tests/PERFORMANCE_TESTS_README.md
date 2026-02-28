# Performance Tests for BharatSahayak

This directory contains comprehensive performance tests for the BharatSahayak system.

## Quick Start

```bash
# Run quick performance check (recommended)
python scripts/run_performance_tests.py quick

# Run all performance tests
python scripts/run_performance_tests.py all

# Verify test setup
python scripts/verify_performance_tests.py
```

## Test File

- **`test_performance.py`** - Main performance test suite with 11 tests

## Test Categories

### 1. Concurrent Load Tests (marked with `slow`)
- Tests system with 1000+ concurrent users
- Measures error rates, response times, resource usage
- Tests: `test_concurrent_user_load_*`

### 2. Response Time Tests
- Validates P95 response time < 3 seconds
- Tests multiple endpoints
- Tests: `test_response_time_*`

### 3. Voice Processing Tests (marked with `voice`)
- Tests STT and TTS latency
- End-to-end voice query flow
- Tests: `test_voice_processing_latency_*`, `test_end_to_end_voice_query_latency`

### 4. Low-Resource Device Tests (marked with `resource`)
- Memory and CPU usage monitoring
- Connection pool performance
- Tests: `test_low_memory_device_performance`, `test_cpu_usage_under_load`, `test_database_connection_pool_performance`

### 5. Stress Tests (marked with `stress` and `slow`)
- Sustained load testing (5+ minutes)
- Performance degradation detection
- Tests: `test_sustained_load_performance`

## Running Tests

### By Category

```bash
# Load tests only
python scripts/run_performance_tests.py load

# Response time tests only
python scripts/run_performance_tests.py response

# Voice processing tests only
python scripts/run_performance_tests.py voice

# Resource tests only
python scripts/run_performance_tests.py resource

# Stress tests only
python scripts/run_performance_tests.py stress
```

### Using pytest Directly

```bash
# All performance tests
pytest test_performance.py -v -m performance -s

# Exclude slow tests
pytest test_performance.py -v -m "performance and not slow" -s

# Only voice tests
pytest test_performance.py -v -m "performance and voice" -s

# Specific test
pytest test_performance.py::test_response_time_95th_percentile_ask_endpoint -v -s
```

## Performance Requirements

| Requirement | Target | Test |
|-------------|--------|------|
| Concurrent Users | 1000+ | `test_concurrent_user_load_*` |
| P95 Response Time | < 3s | `test_response_time_95th_percentile_*` |
| Voice Processing | < 5s | `test_voice_processing_latency_*` |
| Memory Usage | 1GB RAM | `test_low_memory_device_performance` |

## Understanding Results

### Good Performance
```
Response Times:
  Average: 450ms
  P95: 850ms ✓
Error Rate: 0.5% ✓
```

### Performance Issues
```
Response Times:
  Average: 2500ms
  P95: 4500ms ✗ (exceeds 3000ms)
Error Rate: 8.2% ✗ (exceeds 5%)
```

## Metrics Tracked

- **Response Times**: Average, Median (P50), P95, P99
- **Error Rate**: Percentage of failed requests
- **Memory Usage**: Current and peak memory
- **CPU Usage**: Average and peak CPU
- **Throughput**: Requests per second

## Documentation

- **Quick Start**: `PERFORMANCE_TESTING_QUICKSTART.md` (project root)
- **Comprehensive Guide**: `docs/performance_testing_guide.md`
- **Task Summary**: `docs/task_24.3_completion_summary.md`

## Troubleshooting

### Import Errors
Ensure pytest.ini is present in project root with `pythonpath = .`

### Connection Errors
Start the application before running tests:
```bash
uvicorn app.main:app --reload
```

### High Response Times
Check:
- Database connection pool size
- Redis cache configuration
- Query optimization
- External API timeouts

## CI/CD Integration

Add to your pipeline:
```yaml
- name: Performance Tests
  run: python scripts/run_performance_tests.py quick
```

## Requirements

- Python 3.11+
- pytest
- psutil
- FastAPI application running

## Notes

- Tests use mocking for voice processing
- Database tests use test database
- Resource monitoring uses psutil
- Tests marked with appropriate pytest markers
