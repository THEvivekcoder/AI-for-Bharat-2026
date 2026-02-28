# Performance Testing Guide for BharatSahayak

## Overview

This guide covers the performance testing strategy for BharatSahayak, including test execution, metrics interpretation, and optimization recommendations.

## Performance Requirements

Based on Requirement 10.3, the system must meet the following performance criteria:

1. **Concurrent User Load**: Support 1000+ concurrent users
2. **Response Time**: 95th percentile < 3 seconds for API queries
3. **Voice Processing**: End-to-end voice query < 5 seconds
4. **Low-Resource Devices**: Run on devices with 1GB RAM

## Test Categories

### 1. Concurrent Load Tests

Tests system behavior under high concurrent user load.

**Tests:**
- `test_concurrent_user_load_health_endpoint` - 1000+ users on health endpoint
- `test_concurrent_user_load_scheme_search` - 500+ users on scheme search

**Metrics:**
- Response time percentiles (P50, P95, P99)
- Error rate
- Memory usage
- CPU usage

**Success Criteria:**
- Error rate < 5%
- P95 response time reasonable for endpoint type
- System remains stable

### 2. Response Time Tests

Tests that response times meet SLA requirements.

**Tests:**
- `test_response_time_95th_percentile_ask_endpoint` - RAG query response times
- `test_response_time_various_endpoints` - Multiple endpoint response times

**Metrics:**
- Average response time
- Median response time
- P95 response time
- P99 response time

**Success Criteria:**
- P95 < 3000ms for RAG queries
- P95 < 500ms for health endpoint
- Consistent performance across requests

### 3. Voice Processing Tests

Tests voice interface latency.

**Tests:**
- `test_voice_processing_latency_stt` - Speech-to-text latency
- `test_voice_processing_latency_tts` - Text-to-speech latency
- `test_end_to_end_voice_query_latency` - Full voice query flow

**Metrics:**
- STT processing time
- TTS processing time
- End-to-end latency (STT + RAG + TTS)

**Success Criteria:**
- STT P95 < 5000ms
- TTS P95 < 5000ms
- End-to-end P95 < 10000ms

### 4. Low-Resource Device Tests

Tests performance on resource-constrained devices.

**Tests:**
- `test_low_memory_device_performance` - Memory usage monitoring
- `test_cpu_usage_under_load` - CPU usage monitoring
- `test_database_connection_pool_performance` - Connection pool efficiency

**Metrics:**
- Maximum memory usage
- Average CPU usage
- Connection pool exhaustion rate

**Success Criteria:**
- Memory usage stays reasonable
- No connection pool exhaustion
- Stable performance under resource constraints

### 5. Stress Tests

Tests system behavior under sustained load.

**Tests:**
- `test_sustained_load_performance` - 5-minute sustained load test

**Metrics:**
- Performance degradation over time
- Error rate stability
- Resource leak detection

**Success Criteria:**
- No performance degradation over time
- Error rate remains < 5%
- No memory leaks

## Running Performance Tests

### Quick Performance Check

Run fast performance tests (excludes slow and stress tests):

```bash
python scripts/run_performance_tests.py quick
```

### Full Performance Suite

Run all performance tests (may take 10+ minutes):

```bash
python scripts/run_performance_tests.py all
```

### Specific Test Categories

Run specific categories:

```bash
# Load tests only
python scripts/run_performance_tests.py load

# Response time tests only
python scripts/run_performance_tests.py response

# Voice processing tests only
python scripts/run_performance_tests.py voice

# Resource tests only
python scripts/run_performance_tests.py resource

# Stress tests only (long-running)
python scripts/run_performance_tests.py stress
```

### Using pytest Directly

Run with pytest markers:

```bash
# All performance tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m performance

# Exclude slow tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m "performance and not slow"

# Only voice tests
pytest .kiro/specs/bharatsahayak/tests/test_performance.py -v -m "performance and voice"

# Specific test
pytest .kiro/specs/bharatsahayak/tests/test_performance.py::test_concurrent_user_load_health_endpoint -v -s
```

## Interpreting Results

### Response Time Metrics

- **Average**: Mean response time across all requests
- **Median (P50)**: 50% of requests complete faster than this
- **P95**: 95% of requests complete faster than this (SLA metric)
- **P99**: 99% of requests complete faster than this (tail latency)

### Performance Indicators

**Good Performance:**
```
Response Times:
  Average: 450ms
  Median (P50): 380ms
  P95: 850ms
  P99: 1200ms
Error Rate: 0.5%
```

**Degraded Performance:**
```
Response Times:
  Average: 2500ms
  Median (P50): 2100ms
  P95: 4500ms
  P99: 6800ms
Error Rate: 8.2%
```

### Common Issues

**High Error Rate (>5%)**
- Possible causes: Database connection pool exhaustion, timeout issues, resource limits
- Solutions: Increase connection pool size, optimize queries, add caching

**High P95 Response Time**
- Possible causes: Slow database queries, inefficient algorithms, external API delays
- Solutions: Add database indexes, optimize code, implement caching, use async processing

**Memory Growth**
- Possible causes: Memory leaks, large object retention, insufficient garbage collection
- Solutions: Profile memory usage, fix leaks, optimize data structures

**CPU Saturation**
- Possible causes: CPU-intensive operations, inefficient algorithms, lack of caching
- Solutions: Optimize algorithms, add caching, use async I/O, scale horizontally

## Performance Optimization Tips

### 1. Database Optimization

```python
# Add indexes for frequently queried fields
CREATE INDEX idx_schemes_category ON schemes(category);
CREATE INDEX idx_schemes_state ON schemes(state);

# Use connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
```

### 2. Caching Strategy

```python
# Cache frequently accessed data
@cache.memoize(timeout=3600)
def get_popular_schemes():
    return db.query(Scheme).filter(...).all()

# Use Redis for session data
redis_client.setex(f"session:{session_id}", 3600, session_data)
```

### 3. Async Processing

```python
# Use async for I/O-bound operations
async def fetch_external_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 4. Response Compression

```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 5. Query Optimization

```python
# Use select_related to avoid N+1 queries
schemes = db.query(Scheme).options(
    selectinload(Scheme.translations)
).all()

# Limit result sets
schemes = db.query(Scheme).limit(100).all()
```

## Continuous Performance Monitoring

### Setting Up Monitoring

1. **Application Performance Monitoring (APM)**
   - Use tools like New Relic, DataDog, or Prometheus
   - Track response times, error rates, throughput

2. **Database Monitoring**
   - Monitor query performance
   - Track connection pool usage
   - Identify slow queries

3. **Resource Monitoring**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

### Performance Benchmarks

Establish baseline metrics:

```python
# Save baseline metrics
{
    "health_endpoint_p95": 50,
    "scheme_search_p95": 800,
    "rag_query_p95": 2500,
    "concurrent_users_supported": 1000,
    "error_rate_threshold": 5.0
}
```

### Regression Testing

Run performance tests in CI/CD:

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on: [push, pull_request]
jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run quick performance check
        run: python scripts/run_performance_tests.py quick
```

## Load Testing Tools

For more comprehensive load testing, consider:

### 1. Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class BharatSahayakUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search_schemes(self):
        self.client.get("/api/schemes")
    
    @task(3)
    def ask_question(self):
        self.client.post("/api/ask", json={
            "query": "What schemes are available?",
            "language": "en"
        })
```

Run: `locust -f locustfile.py --host=http://localhost:8000`

### 2. Apache Bench

```bash
# Test health endpoint
ab -n 1000 -c 100 http://localhost:8000/health

# Test with POST data
ab -n 100 -c 10 -p query.json -T application/json http://localhost:8000/api/ask
```

### 3. wrk

```bash
# Test with 100 connections for 30 seconds
wrk -t12 -c100 -d30s http://localhost:8000/health
```

## Performance Test Checklist

Before deploying to production:

- [ ] All performance tests pass
- [ ] P95 response time < 3 seconds for critical endpoints
- [ ] System handles 1000+ concurrent users
- [ ] Error rate < 5% under load
- [ ] No memory leaks detected
- [ ] Voice processing latency acceptable
- [ ] Database queries optimized
- [ ] Caching implemented for hot paths
- [ ] Connection pools properly sized
- [ ] Monitoring and alerting configured

## Troubleshooting

### Test Failures

**"P95 response time exceeds threshold"**
- Check database query performance
- Review application logs for slow operations
- Profile code to identify bottlenecks

**"High error rate under load"**
- Check for connection pool exhaustion
- Review error logs for patterns
- Verify external service availability

**"Memory usage too high"**
- Profile memory usage
- Check for memory leaks
- Review object lifecycle management

### Getting Help

If performance tests consistently fail:

1. Review application logs
2. Check system resource usage
3. Profile the application
4. Optimize identified bottlenecks
5. Re-run tests to verify improvements

## References

- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [Python Profiling](https://docs.python.org/3/library/profile.html)
- [Load Testing Best Practices](https://www.nginx.com/blog/load-testing-best-practices/)
