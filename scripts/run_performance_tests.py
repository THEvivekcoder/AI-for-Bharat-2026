#!/usr/bin/env python3
"""
Performance Test Runner for BharatSahayak

This script runs performance tests and generates a detailed report.
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path


def run_performance_tests(test_type="all"):
    """
    Run performance tests and generate report
    
    Args:
        test_type: Type of tests to run (all, load, response, voice, resource, stress)
    """
    print("="*70)
    print("BharatSahayak Performance Test Suite")
    print("="*70)
    print(f"Test Type: {test_type}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Determine which tests to run
    if test_type == "all":
        markers = "performance"
    elif test_type == "load":
        markers = "performance and not slow and not stress"
    elif test_type == "response":
        markers = "performance and not voice and not resource and not stress"
    elif test_type == "voice":
        markers = "performance and voice"
    elif test_type == "resource":
        markers = "performance and resource"
    elif test_type == "stress":
        markers = "performance and stress"
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
    
    # Run pytest with performance markers
    cmd = [
        "pytest",
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        "-v",
        "-m", markers,
        "--tb=short",
        "-s"  # Show print statements
    ]
    
    print(f"\nRunning command: {' '.join(cmd)}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    duration = time.time() - start_time
    
    print("\n" + "="*70)
    print(f"Test Duration: {duration:.2f} seconds")
    print(f"Exit Code: {result.returncode}")
    print("="*70)
    
    return result.returncode


def run_quick_performance_check():
    """Run a quick performance check (non-slow tests only)"""
    print("="*70)
    print("Quick Performance Check")
    print("="*70)
    
    cmd = [
        "pytest",
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        "-v",
        "-m", "performance and not slow and not stress",
        "--tb=short",
        "-s"
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_load_test_only():
    """Run only the concurrent load tests"""
    print("="*70)
    print("Concurrent Load Tests")
    print("="*70)
    
    cmd = [
        "pytest",
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        "-v",
        "-k", "concurrent",
        "--tb=short",
        "-s"
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "quick":
            exit_code = run_quick_performance_check()
        elif test_type == "load-only":
            exit_code = run_load_test_only()
        else:
            exit_code = run_performance_tests(test_type)
    else:
        # Default: run quick check
        print("Usage: python scripts/run_performance_tests.py [test_type]")
        print("\nTest types:")
        print("  quick       - Quick performance check (no slow tests)")
        print("  all         - All performance tests")
        print("  load        - Concurrent load tests")
        print("  load-only   - Only concurrent load tests")
        print("  response    - Response time tests")
        print("  voice       - Voice processing tests")
        print("  resource    - Low-resource device tests")
        print("  stress      - Stress tests (long-running)")
        print("\nRunning quick check by default...\n")
        
        exit_code = run_quick_performance_check()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
