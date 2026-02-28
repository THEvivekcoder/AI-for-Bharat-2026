#!/usr/bin/env python3
"""
Test runner for PWA integration tests.

This script runs the PWA integration tests and provides a summary of results.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_simple_tests():
    """Run simplified PWA integration tests."""
    print("=" * 70)
    print("Running PWA Integration Tests (Simplified)")
    print("=" * 70)
    print()
    
    test_file = ".kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run(
            ["pytest", test_file, "-v", "--tb=short", "--color=yes"],
            capture_output=False,
            text=True
        )
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_browser_tests():
    """Run browser-based PWA integration tests (requires Playwright)."""
    print()
    print("=" * 70)
    print("Running PWA Integration Tests (Browser-based)")
    print("=" * 70)
    print()
    
    test_file = ".kiro/specs/bharatsahayak/tests/test_integration_pwa.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    # Check if Playwright is installed
    try:
        import playwright
    except ImportError:
        print("⚠️  Playwright not installed. Skipping browser tests.")
        print("   To install: pip install playwright && playwright install")
        return None
    
    try:
        result = subprocess.run(
            ["pytest", test_file, "-v", "--tb=short", "--color=yes"],
            capture_output=False,
            text=True
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running browser tests: {e}")
        return False


def check_pwa_files():
    """Check that PWA files exist."""
    print()
    print("=" * 70)
    print("Checking PWA Files")
    print("=" * 70)
    print()
    
    required_files = [
        "frontend/index.html",
        "frontend/manifest.json",
        "frontend/sw.js",
        "frontend/js/app.js",
        "frontend/js/api.js",
        "frontend/js/voice.js",
        "frontend/js/chat.js",
        "frontend/js/offline.js",
        "frontend/css/styles.css"
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False
    
    print()
    
    if all_exist:
        print("✓ All PWA files present")
    else:
        print("⚠️  Some PWA files are missing")
    
    return all_exist


def main():
    """Main test runner."""
    print()
    print("PWA Integration Test Suite")
    print("=" * 70)
    print()
    
    # Check PWA files
    files_ok = check_pwa_files()
    
    # Run simplified tests
    simple_tests_ok = run_simple_tests()
    
    # Run browser tests (optional)
    browser_tests_ok = run_browser_tests()
    
    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()
    
    print(f"PWA Files:        {'✓ PASS' if files_ok else '✗ FAIL'}")
    print(f"Simple Tests:     {'✓ PASS' if simple_tests_ok else '✗ FAIL'}")
    
    if browser_tests_ok is not None:
        print(f"Browser Tests:    {'✓ PASS' if browser_tests_ok else '✗ FAIL'}")
    else:
        print(f"Browser Tests:    ⊘ SKIPPED")
    
    print()
    
    # Exit code
    if simple_tests_ok and files_ok:
        print("✓ PWA integration tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
