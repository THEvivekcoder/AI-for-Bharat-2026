# Task 24.3 Completion Summary: Performance Tests

## Overview

Implemented comprehensive performance tests for BharatSahayak covering concurrent user load, response times, voice processing latency, and low-resource device performance.

## Files Created

### 1. Test Implementation
- **`.kiro/specs/bharatsahayak/tests/test_performance.py`**
  - Comprehensive performance test suite
  - 11 performance tests covering all requirements
  - Includes metrics tracking and reporting

### 2. Test Runner Script
- **`scripts/run_performance_tests.py`**
  - Convenient script to run performance tests
  - Supports different test categories
  - Provides formatted output

### 3. Documentation
- **`docs/performance_testing_guide.md`**
  - Comprehensive guide to performance testing
  - Metrics interpretation
  - Optimization recommendations
  - Troubleshooting guide

- **`PERFORMANCE_TESTING_QUICKSTART.md`**
  - Quick start guide for running tests
  - Common commands and examples
  - Understanding results

### 4. Configuration
- **`.kiro/specs/bharatsahayak/tests/conftest.py`**
  - Pytest configuration for performance tests
  - Python path setup
  - Test environment configuration

- **`pytest.ini`**
  - Project-level pytest configuration
  - Test discovery patterns
  - Marker definitions
  - Python path configuration

- **`requirements.txt`** (updated)
  - Added `psutil==5.9.8` for resource monitoring

## Test Categories

### 1. Concurrent Load Tests
- `test_concurrent_user_load_health_endpoint` - 1000+ users on health endpoint
- `test_concurrent_user_load_scheme_search` - 500+ users on scheme search
- Tests error rates, response times, memory, and CPU usage

### 2. Response Time Tests
- `test_response_time_95th_percentile_ask_endpoint` - RAG query P95 < 3s
- `test_response_time_various_endpoints` - Multiple endpoint response times
- Validates SLA requirements

### 3. Voice Processing Tests
- `test_voice_processing_latency_stt` - Speech-to-text latency
- `test_voice_processing_latency_tts` - Text-to-speech latency
- `test_end_to_end_voice_query_latency` - Full voice query flow
- Target: < 5 seconds for voice processing

### 4. Low-Resource Device Tests
- `test_low_memory_device_performance` - Memory usage monitoring
- `test_cpu_usage_under_load` - CPU usage monitoring
- `test_database_connection_pool_performance` - Connection pool efficiency
- Validates 1GB RAM requirement

### 5. Stress Tests
- `test_sustained_load_performance` - 5-minute sustained load test
- Detects performance degradation and resource leaks

## Performance Metrics Tracked

### Response Time Metrics
- Average response time
- Median (P50)
- 95th percentile (P95) - SLA metric
- 99th percentile (P99) - tail latency

### Resource Metrics
- Memory usage (current and peak)
- CPU usage (average and peak)
- Error rate
- Throughput (requests per second)

### Success Criteria
- P95 response time < 3000ms for RAG queries
- Error rate < 5% under load
- System handles 1000+ concurrent users
- Voice processing < 5000ms
- Works on devices with 1GB RAM

## Running Performance Tests

### Quick Check (Recommended)
```bash
python scripts/run_performance_tests.py quick
```

### Full Suite
```bash
python scripts/run_performance_tests.py all
```

### Specific Categories
```bash
# Load tests
python scripts/run_performance_tests.py load

# Response time tests
python scripts/run_performance_tests.py response

# Voice processing tests
python scripts/run_performance_tests.py voice

# Resource tests
python scripts/run_performance_tests.py resource

# Stress tests
python scripts/run_performance_tests.py stress
```

### Using pytest Directly
```bash
# All performance tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m performance -s

# Exclude slow tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m "performance and not slow" -s

# Specific test
pytest .kiro/specs/bharatsahayak/tests/test_performance.py::test_response_time_95th_percentile_ask_endpoint -v -s
```

## Key Features

### 1. PerformanceMetrics Class
- Tracks response times, errors, memory, and CPU usage
- Calculates percentiles (P50, P95, P99)
- Computes error rates and averages
- Provides comprehensive performance analysis

### 2. Concurrent User Simulation
- Uses ThreadPoolExecutor for concurrent requests
- Configurable number of concurrent users
- Tracks system resources during load
- Measures error rates and response times

### 3. Resource Monitoring
- Real-time memory usage tracking
- CPU usage monitoring
- Connection pool monitoring
- Low-resource device simulation

### 4. Comprehensive Reporting
- Detailed performance metrics output
- Clear pass/fail criteria
- Actionable insights
- Performance trends

## Performance Requirements Validation

| Requirement | Test | Status |
|-------------|------|--------|
| 1000+ concurrent users | `test_concurrent_user_load_*` | ✓ Implemented |
| P95 < 3 seconds | `test_response_time_95th_percentile_*` | ✓ Implemented |
| Voice processing < 5s | `test_voice_processing_latency_*` | ✓ Implemented |
| Works on 1GB RAM | `test_low_memory_device_performance` | ✓ Implemented |

## Example Output

```
============================================================
Testing concurrent load: 1000 users
============================================================

Results for 1000 concurrent users:
  Response Times:
    Average: 450.23ms
    Median (P50): 380.15ms
    P95: 850.67ms
    P99: 1200.34ms
  Error Rate: 0.50%
  Max Memory: 512.45MB
  Avg CPU: 45.23%
```

## Integration with CI/CD

Performance tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/performance.yml
- name: Run Performance Tests
  run: python scripts/run_performance_tests.py quick
```

## Optimization Recommendations

The guide includes recommendations for:
1. Database optimization (indexes, connection pooling)
2. Caching strategies (Redis, in-memory)
3. Async processing for I/O-bound operations
4. Response compression
5. Query optimization

## Troubleshooting

Common issues and solutions documented:
- High error rates → Check connection pools
- High P95 times → Optimize queries, add caching
- Memory growth → Profile and fix leaks
- CPU saturation → Optimize algorithms, add caching

## Next Steps

1. Run quick performance check to establish baseline
2. Run full suite before deployment
3. Set up continuous monitoring
4. Optimize based on results
5. Integrate into CI/CD pipeline

## Requirements Satisfied

✓ Test concurrent user load (1000+ users)
✓ Test response time (< 3 seconds for 95th percentile)
✓ Test voice processing latency
✓ Test low-resource device performance
✓ Requirements: 10.3

## Notes

- Tests use mocking for voice processing to avoid dependency on actual models
- Database tests use test database to avoid affecting production data
- Resource monitoring uses psutil for accurate measurements
- Tests are marked with pytest markers for selective execution
- Comprehensive documentation provided for maintenance and extension
