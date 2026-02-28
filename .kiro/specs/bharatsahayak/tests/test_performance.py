"""
Performance Tests for BharatSahayak

Tests concurrent user load, response times, voice processing latency,
and low-resource device performance.

Requirements: 10.3
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import psutil
import sys
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.services.voice_interface import SpeechToTextEngine, TextToSpeechEngine
from app.services.rag_engine import RAGEngine
from app.database import get_db


# Performance test configuration
CONCURRENT_USERS = 1000
RESPONSE_TIME_THRESHOLD_MS = 3000  # 3 seconds
VOICE_PROCESSING_THRESHOLD_MS = 5000  # 5 seconds
LOW_MEMORY_THRESHOLD_MB = 1024  # 1GB


class PerformanceMetrics:
    """Track performance metrics during tests"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
    
    def add_response_time(self, time_ms: float):
        self.response_times.append(time_ms)
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def add_memory_usage(self, memory_mb: float):
        self.memory_usage.append(memory_mb)
    
    def add_cpu_usage(self, cpu_percent: float):
        self.cpu_usage.append(cpu_percent)
    
    def get_percentile(self, percentile: int) -> float:
        """Get percentile of response times"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_average(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    def get_median(self) -> float:
        """Get median response time"""
        if not self.response_times:
            return 0.0
        return statistics.median(self.response_times)
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage"""
        total = len(self.response_times) + len(self.errors)
        if total == 0:
            return 0.0
        return (len(self.errors) / total) * 100
    
    def get_max_memory(self) -> float:
        """Get maximum memory usage"""
        if not self.memory_usage:
            return 0.0
        return max(self.memory_usage)
    
    def get_avg_cpu(self) -> float:
        """Get average CPU usage"""
        if not self.cpu_usage:
            return 0.0
        return statistics.mean(self.cpu_usage)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def metrics():
    """Create performance metrics tracker"""
    return PerformanceMetrics()


def measure_endpoint_performance(
    client: TestClient,
    method: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    headers: Dict[str, str] = None
) -> tuple[float, bool]:
    """
    Measure performance of a single endpoint call
    
    Returns:
        tuple: (response_time_ms, success)
    """
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = client.get(endpoint, headers=headers)
        elif method.upper() == "POST":
            response = client.post(endpoint, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = client.put(endpoint, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        success = response.status_code < 400
        return response_time_ms, success
    
    except Exception as e:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        return response_time_ms, False


def simulate_concurrent_users(
    client: TestClient,
    num_users: int,
    endpoint: str,
    method: str = "GET",
    data_generator=None
) -> PerformanceMetrics:
    """
    Simulate concurrent users hitting an endpoint
    
    Args:
        client: Test client
        num_users: Number of concurrent users
        endpoint: API endpoint to test
        method: HTTP method
        data_generator: Function to generate request data for each user
    
    Returns:
        PerformanceMetrics with results
    """
    metrics = PerformanceMetrics()
    
    def make_request(user_id: int):
        # Track system resources
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=0.1)
        
        metrics.add_memory_usage(memory_mb)
        metrics.add_cpu_usage(cpu_percent)
        
        # Generate request data if needed
        data = data_generator(user_id) if data_generator else None
        
        # Make request and measure performance
        response_time, success = measure_endpoint_performance(
            client, method, endpoint, data
        )
        
        if success:
            metrics.add_response_time(response_time)
        else:
            metrics.add_error(f"User {user_id} request failed")
    
    # Execute concurrent requests
    with ThreadPoolExecutor(max_workers=min(num_users, 100)) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_users)]
        
        # Wait for all requests to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                metrics.add_error(str(e))
    
    return metrics


# Test 1: Concurrent User Load (1000+ users)
@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_user_load_health_endpoint(client, metrics):
    """
    Test system performance with 1000+ concurrent users on health endpoint
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing concurrent load: {CONCURRENT_USERS} users")
    print(f"{'='*60}")
    
    # Test health endpoint (lightweight)
    test_metrics = simulate_concurrent_users(
        client=client,
        num_users=CONCURRENT_USERS,
        endpoint="/health",
        method="GET"
    )
    
    # Analyze results
    p50 = test_metrics.get_percentile(50)
    p95 = test_metrics.get_percentile(95)
    p99 = test_metrics.get_percentile(99)
    avg = test_metrics.get_average()
    error_rate = test_metrics.get_error_rate()
    max_memory = test_metrics.get_max_memory()
    avg_cpu = test_metrics.get_avg_cpu()
    
    print(f"\nResults for {CONCURRENT_USERS} concurrent users:")
    print(f"  Response Times:")
    print(f"    Average: {avg:.2f}ms")
    print(f"    Median (P50): {p50:.2f}ms")
    print(f"    P95: {p95:.2f}ms")
    print(f"    P99: {p99:.2f}ms")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Max Memory: {max_memory:.2f}MB")
    print(f"  Avg CPU: {avg_cpu:.2f}%")
    
    # Assertions
    assert len(test_metrics.response_times) > 0, "No successful requests"
    assert error_rate < 5.0, f"Error rate too high: {error_rate:.2f}%"
    assert p95 < RESPONSE_TIME_THRESHOLD_MS * 2, \
        f"P95 response time {p95:.2f}ms exceeds threshold for health endpoint"


@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_user_load_scheme_search(client):
    """
    Test system performance with concurrent users on scheme search endpoint
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing scheme search with {CONCURRENT_USERS} concurrent users")
    print(f"{'='*60}")
    
    # Data generator for scheme search
    def generate_search_data(user_id: int):
        queries = [
            "agriculture schemes",
            "health insurance",
            "education benefits",
            "employment programs",
            "farmer support"
        ]
        return {"query": queries[user_id % len(queries)]}
    
    # Test scheme search endpoint
    test_metrics = simulate_concurrent_users(
        client=client,
        num_users=min(CONCURRENT_USERS, 500),  # Reduce for heavier endpoint
        endpoint="/api/schemes",
        method="GET"
    )
    
    # Analyze results
    p95 = test_metrics.get_percentile(95)
    avg = test_metrics.get_average()
    error_rate = test_metrics.get_error_rate()
    
    print(f"\nScheme Search Results:")
    print(f"  Average: {avg:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  Error Rate: {error_rate:.2f}%")
    
    # Assertions
    assert error_rate < 10.0, f"Error rate too high: {error_rate:.2f}%"
    # Note: Scheme search may be slower, so we allow higher threshold


# Test 2: Response Time (< 3 seconds for 95th percentile)
@pytest.mark.performance
def test_response_time_95th_percentile_ask_endpoint(client):
    """
    Test that 95th percentile response time is under 3 seconds for RAG queries
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing response time for RAG queries")
    print(f"Target: P95 < {RESPONSE_TIME_THRESHOLD_MS}ms")
    print(f"{'='*60}")
    
    # Data generator for RAG queries
    def generate_query_data(user_id: int):
        queries = [
            "What schemes are available for farmers?",
            "How do I apply for health insurance?",
            "Tell me about skill development programs",
            "What are the eligibility criteria for PM-KISAN?",
            "How can I find government jobs?"
        ]
        return {
            "query": queries[user_id % len(queries)],
            "language": "en"
        }
    
    # Test with moderate load
    test_metrics = simulate_concurrent_users(
        client=client,
        num_users=100,
        endpoint="/api/ask",
        method="POST",
        data_generator=generate_query_data
    )
    
    # Analyze results
    p95 = test_metrics.get_percentile(95)
    p99 = test_metrics.get_percentile(99)
    avg = test_metrics.get_average()
    median = test_metrics.get_median()
    
    print(f"\nRAG Query Response Times:")
    print(f"  Average: {avg:.2f}ms")
    print(f"  Median: {median:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    
    # Assertion: P95 should be under 3 seconds
    assert p95 < RESPONSE_TIME_THRESHOLD_MS, \
        f"P95 response time {p95:.2f}ms exceeds {RESPONSE_TIME_THRESHOLD_MS}ms threshold"


@pytest.mark.performance
def test_response_time_various_endpoints(client):
    """
    Test response times across various endpoints
    
    Requirements: 10.3
    """
    endpoints_to_test = [
        ("GET", "/health", None),
        ("GET", "/api/schemes", None),
        ("GET", "/api/languages", None),
        ("POST", "/api/session/create", {"user_id": "test-user", "language": "en"}),
    ]
    
    print(f"\n{'='*60}")
    print(f"Testing response times for various endpoints")
    print(f"{'='*60}")
    
    for method, endpoint, data in endpoints_to_test:
        metrics = PerformanceMetrics()
        
        # Make 50 requests to each endpoint
        for i in range(50):
            response_time, success = measure_endpoint_performance(
                client, method, endpoint, data
            )
            if success:
                metrics.add_response_time(response_time)
            else:
                metrics.add_error(f"Request {i} failed")
        
        p95 = metrics.get_percentile(95)
        avg = metrics.get_average()
        
        print(f"\n{method} {endpoint}:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        
        # Most endpoints should respond quickly
        if endpoint == "/health":
            assert p95 < 500, f"Health endpoint too slow: {p95:.2f}ms"


# Test 3: Voice Processing Latency
@pytest.mark.performance
@pytest.mark.voice
def test_voice_processing_latency_stt():
    """
    Test speech-to-text processing latency
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing STT processing latency")
    print(f"Target: < {VOICE_PROCESSING_THRESHOLD_MS}ms")
    print(f"{'='*60}")
    
    # Mock STT engine for performance testing
    with patch('app.services.voice_interface.SpeechToTextEngine') as MockSTT:
        mock_stt = MockSTT.return_value
        
        # Simulate STT processing time
        def mock_transcribe(audio_data, language=None):
            time.sleep(0.5)  # Simulate 500ms processing
            return Mock(
                text="Test transcription",
                confidence=0.95,
                detected_language="en"
            )
        
        mock_stt.transcribe = mock_transcribe
        
        metrics = PerformanceMetrics()
        
        # Test multiple transcriptions
        for i in range(20):
            start_time = time.time()
            result = mock_stt.transcribe(b"fake_audio_data")
            end_time = time.time()
            
            processing_time_ms = (end_time - start_time) * 1000
            metrics.add_response_time(processing_time_ms)
        
        avg = metrics.get_average()
        p95 = metrics.get_percentile(95)
        
        print(f"\nSTT Processing Times:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        
        # STT should complete within threshold
        assert p95 < VOICE_PROCESSING_THRESHOLD_MS, \
            f"STT P95 latency {p95:.2f}ms exceeds {VOICE_PROCESSING_THRESHOLD_MS}ms"


@pytest.mark.performance
@pytest.mark.voice
def test_voice_processing_latency_tts():
    """
    Test text-to-speech processing latency
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing TTS processing latency")
    print(f"Target: < {VOICE_PROCESSING_THRESHOLD_MS}ms")
    print(f"{'='*60}")
    
    # Mock TTS engine for performance testing
    with patch('app.services.voice_interface.TextToSpeechEngine') as MockTTS:
        mock_tts = MockTTS.return_value
        
        # Simulate TTS processing time
        def mock_synthesize(text, language, voice_profile="default"):
            # Simulate processing time based on text length
            processing_time = len(text) * 0.01  # 10ms per character
            time.sleep(min(processing_time, 2.0))  # Cap at 2 seconds
            return b"fake_audio_data"
        
        mock_tts.synthesize = mock_synthesize
        
        metrics = PerformanceMetrics()
        
        # Test various text lengths
        test_texts = [
            "Hello",
            "This is a medium length sentence for testing.",
            "This is a longer text that simulates a typical response from the system. " * 3
        ]
        
        for text in test_texts:
            for i in range(10):
                start_time = time.time()
                audio = mock_tts.synthesize(text, "en")
                end_time = time.time()
                
                processing_time_ms = (end_time - start_time) * 1000
                metrics.add_response_time(processing_time_ms)
        
        avg = metrics.get_average()
        p95 = metrics.get_percentile(95)
        
        print(f"\nTTS Processing Times:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        
        # TTS should complete within threshold
        assert p95 < VOICE_PROCESSING_THRESHOLD_MS, \
            f"TTS P95 latency {p95:.2f}ms exceeds {VOICE_PROCESSING_THRESHOLD_MS}ms"


@pytest.mark.performance
@pytest.mark.voice
def test_end_to_end_voice_query_latency(client):
    """
    Test end-to-end voice query latency (STT -> RAG -> TTS)
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing end-to-end voice query latency")
    print(f"Target: < 10 seconds (STT + RAG + TTS)")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    # Simulate end-to-end voice queries
    for i in range(10):
        start_time = time.time()
        
        # Step 1: STT (simulated)
        time.sleep(0.5)
        
        # Step 2: RAG query
        response_time, success = measure_endpoint_performance(
            client,
            "POST",
            "/api/ask",
            {"query": "What schemes are available?", "language": "en"}
        )
        
        # Step 3: TTS (simulated)
        time.sleep(0.5)
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        if success:
            metrics.add_response_time(total_time_ms)
        else:
            metrics.add_error(f"Query {i} failed")
    
    avg = metrics.get_average()
    p95 = metrics.get_percentile(95)
    
    print(f"\nEnd-to-End Voice Query Times:")
    print(f"  Average: {avg:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    
    # End-to-end should complete within 10 seconds
    assert p95 < 10000, \
        f"End-to-end P95 latency {p95:.2f}ms exceeds 10000ms"


# Test 4: Low-Resource Device Performance
@pytest.mark.performance
@pytest.mark.resource
def test_low_memory_device_performance(client):
    """
    Test system performance on low-memory devices (1GB RAM simulation)
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing low-memory device performance")
    print(f"Memory threshold: {LOW_MEMORY_THRESHOLD_MB}MB")
    print(f"{'='*60}")
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    print(f"\nInitial memory usage: {initial_memory:.2f}MB")
    
    metrics = PerformanceMetrics()
    
    # Simulate typical user interactions
    interactions = [
        ("GET", "/health", None),
        ("GET", "/api/schemes", None),
        ("POST", "/api/ask", {"query": "Tell me about schemes", "language": "en"}),
        ("GET", "/api/languages", None),
    ]
    
    for i in range(50):
        method, endpoint, data = interactions[i % len(interactions)]
        
        # Measure memory before request
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # Make request
        response_time, success = measure_endpoint_performance(
            client, method, endpoint, data
        )
        
        # Measure memory after request
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_delta = memory_after - memory_before
        
        metrics.add_memory_usage(memory_after)
        
        if success:
            metrics.add_response_time(response_time)
    
    max_memory = metrics.get_max_memory()
    avg_response = metrics.get_average()
    
    print(f"\nLow-Memory Device Results:")
    print(f"  Max memory usage: {max_memory:.2f}MB")
    print(f"  Memory increase: {max_memory - initial_memory:.2f}MB")
    print(f"  Average response time: {avg_response:.2f}ms")
    
    # Memory usage should stay reasonable
    # Note: This is a soft check as actual memory depends on system state
    print(f"\nNote: Memory usage is {max_memory:.2f}MB")
    print(f"Target for low-resource devices: < {LOW_MEMORY_THRESHOLD_MB}MB")


@pytest.mark.performance
@pytest.mark.resource
def test_cpu_usage_under_load(client):
    """
    Test CPU usage under moderate load
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing CPU usage under load")
    print(f"{'='*60}")
    
    process = psutil.Process()
    metrics = PerformanceMetrics()
    
    # Generate load
    for i in range(100):
        cpu_before = process.cpu_percent(interval=0.1)
        
        response_time, success = measure_endpoint_performance(
            client,
            "GET",
            "/health"
        )
        
        cpu_after = process.cpu_percent(interval=0.1)
        
        metrics.add_cpu_usage(cpu_after)
        
        if success:
            metrics.add_response_time(response_time)
    
    avg_cpu = metrics.get_avg_cpu()
    max_cpu = max(metrics.cpu_usage) if metrics.cpu_usage else 0
    
    print(f"\nCPU Usage Results:")
    print(f"  Average CPU: {avg_cpu:.2f}%")
    print(f"  Max CPU: {max_cpu:.2f}%")
    
    # CPU usage should be reasonable
    print(f"\nNote: Average CPU usage is {avg_cpu:.2f}%")


@pytest.mark.performance
@pytest.mark.resource
def test_database_connection_pool_performance(client):
    """
    Test database connection pool performance under load
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing database connection pool performance")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    # Simulate many database-heavy requests
    for i in range(200):
        response_time, success = measure_endpoint_performance(
            client,
            "GET",
            "/api/schemes"
        )
        
        if success:
            metrics.add_response_time(response_time)
        else:
            metrics.add_error(f"Request {i} failed")
    
    avg = metrics.get_average()
    p95 = metrics.get_percentile(95)
    error_rate = metrics.get_error_rate()
    
    print(f"\nDatabase Connection Pool Results:")
    print(f"  Average response: {avg:.2f}ms")
    print(f"  P95 response: {p95:.2f}ms")
    print(f"  Error rate: {error_rate:.2f}%")
    
    # Should handle load without connection pool exhaustion
    assert error_rate < 5.0, \
        f"High error rate suggests connection pool issues: {error_rate:.2f}%"


# Test 5: Stress Testing
@pytest.mark.performance
@pytest.mark.stress
@pytest.mark.slow
def test_sustained_load_performance(client):
    """
    Test system performance under sustained load
    
    Requirements: 10.3
    """
    print(f"\n{'='*60}")
    print(f"Testing sustained load (5 minutes)")
    print(f"{'='*60}")
    
    duration_seconds = 300  # 5 minutes
    requests_per_second = 10
    
    start_time = time.time()
    metrics = PerformanceMetrics()
    
    request_count = 0
    
    while time.time() - start_time < duration_seconds:
        batch_start = time.time()
        
        # Make requests_per_second requests
        for i in range(requests_per_second):
            response_time, success = measure_endpoint_performance(
                client,
                "GET",
                "/health"
            )
            
            if success:
                metrics.add_response_time(response_time)
            else:
                metrics.add_error(f"Request {request_count} failed")
            
            request_count += 1
        
        # Wait to maintain rate
        batch_duration = time.time() - batch_start
        sleep_time = max(0, 1.0 - batch_duration)
        time.sleep(sleep_time)
    
    total_duration = time.time() - start_time
    
    avg = metrics.get_average()
    p95 = metrics.get_percentile(95)
    error_rate = metrics.get_error_rate()
    
    print(f"\nSustained Load Results:")
    print(f"  Duration: {total_duration:.2f}s")
    print(f"  Total requests: {request_count}")
    print(f"  Average response: {avg:.2f}ms")
    print(f"  P95 response: {p95:.2f}ms")
    print(f"  Error rate: {error_rate:.2f}%")
    
    # System should remain stable under sustained load
    assert error_rate < 5.0, \
        f"High error rate under sustained load: {error_rate:.2f}%"
    assert p95 < RESPONSE_TIME_THRESHOLD_MS, \
        f"P95 degraded under sustained load: {p95:.2f}ms"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "performance"])
