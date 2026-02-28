# Performance Testing Quick Start

Quick guide to running performance tests for BharatSahayak.

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure the application is running
python app/main.py
```

## Quick Performance Check (Recommended)

Run fast performance tests (2-3 minutes):

```bash
python scripts/run_performance_tests.py quick
```

This runs:
- Response time tests
- Basic load tests (100 users)
- Resource usage tests

## Full Performance Suite

Run all performance tests including stress tests (10-15 minutes):

```bash
python scripts/run_performance_tests.py all
```

## Specific Test Categories

### Concurrent Load Tests

Test with 1000+ concurrent users:

```bash
python scripts/run_performance_tests.py load
```

### Response Time Tests

Test API response times:

```bash
python scripts/run_performance_tests.py response
```

### Voice Processing Tests

Test STT/TTS latency:

```bash
python scripts/run_performance_tests.py voice
```

### Low-Resource Device Tests

Test memory and CPU usage:

```bash
python scripts/run_performance_tests.py resource
```

### Stress Tests

Test sustained load (5+ minutes):

```bash
python scripts/run_performance_tests.py stress
```

## Using pytest Directly

```bash
# All performance tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m performance -s

# Exclude slow tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m "performance and not slow" -s

# Specific test
pytest .kiro/specs/bharatsahayak/tests/test_performance.py::test_response_time_95th_percentile_ask_endpoint -v -s
```

## Understanding Results

### Good Performance Example

```
Response Times:
  Average: 450ms
  Median (P50): 380ms
  P95: 850ms ✓ (< 3000ms threshold)
  P99: 1200ms
Error Rate: 0.5% ✓ (< 5% threshold)
```

### Performance Issue Example

```
Response Times:
  Average: 2500ms
  P95: 4500ms ✗ (exceeds 3000ms threshold)
Error Rate: 8.2% ✗ (exceeds 5% threshold)
```

## Performance Requirements

| Metric | Requirement | Test |
|--------|-------------|------|
| Concurrent Users | 1000+ | `test_concurrent_user_load_*` |
| P95 Response Time | < 3 seconds | `test_response_time_95th_percentile_*` |
| Voice Processing | < 5 seconds | `test_voice_processing_latency_*` |
| Memory Usage | Works on 1GB RAM | `test_low_memory_device_performance` |

## Troubleshooting

### Tests Fail with Connection Errors

Ensure the application is running:

```bash
# Terminal 1: Start the application
uvicorn app.main:app --reload

# Terminal 2: Run tests
python scripts/run_performance_tests.py quick
```

### High Response Times

Check:
1. Database connection pool size
2. Redis cache configuration
3. External API timeouts
4. Query optimization

### High Error Rates

Check:
1. Application logs for errors
2. Database connection limits
3. Memory/CPU resources
4. Network connectivity

## Next Steps

- Review detailed guide: `docs/performance_testing_guide.md`
- Optimize based on results
- Set up continuous monitoring
- Run tests before each deployment

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/performance.yml
- name: Run Performance Tests
  run: python scripts/run_performance_tests.py quick
```

## Getting Help

If performance tests fail:
1. Check application logs
2. Review `docs/performance_testing_guide.md`
3. Profile the application
4. Optimize identified bottlenecks
