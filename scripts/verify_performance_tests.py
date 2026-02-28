#!/usr/bin/env python3
"""
Verification script for performance tests

This script verifies that performance tests are properly set up and can be run.
"""

import subprocess
import sys
from pathlib import Path


def check_file_exists(filepath):
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {filepath} exists")
        return True
    else:
        print(f"✗ {filepath} missing")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    
    try:
        import psutil
        print(f"✓ psutil installed (version {psutil.__version__})")
    except ImportError:
        print("✗ psutil not installed")
        return False
    
    try:
        import pytest
        print(f"✓ pytest installed (version {pytest.__version__})")
    except ImportError:
        print("✗ pytest not installed")
        return False
    
    return True


def check_test_collection():
    """Check if tests can be collected"""
    print("\nChecking test collection...")
    
    cmd = [
        "pytest",
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        "--collect-only",
        "-q"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Count collected tests
        lines = result.stdout.split('\n')
        for line in lines:
            if 'selected' in line or 'collected' in line:
                print(f"✓ Tests collected: {line.strip()}")
                return True
        print("✓ Tests collected successfully")
        return True
    else:
        print(f"✗ Test collection failed")
        print(result.stderr)
        return False


def list_available_tests():
    """List all available performance tests"""
    print("\nAvailable performance tests:")
    
    cmd = [
        "pytest",
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        "--collect-only",
        "-q"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        test_count = 0
        for line in lines:
            if '::test_' in line:
                test_name = line.split('::')[-1].strip()
                print(f"  - {test_name}")
                test_count += 1
        print(f"\nTotal: {test_count} performance tests")
    else:
        print("Could not list tests")


def main():
    """Main verification function"""
    print("="*70)
    print("Performance Tests Verification")
    print("="*70)
    
    all_checks_passed = True
    
    # Check files
    print("\nChecking files...")
    files_to_check = [
        ".kiro/specs/bharatsahayak/tests/test_performance.py",
        ".kiro/specs/bharatsahayak/tests/conftest.py",
        "scripts/run_performance_tests.py",
        "docs/performance_testing_guide.md",
        "PERFORMANCE_TESTING_QUICKSTART.md"
    ]
    
    for filepath in files_to_check:
        if not check_file_exists(filepath):
            all_checks_passed = False
    
    # Check dependencies
    if not check_dependencies():
        all_checks_passed = False
    
    # Check test collection
    if not check_test_collection():
        all_checks_passed = False
    
    # List available tests
    list_available_tests()
    
    # Summary
    print("\n" + "="*70)
    if all_checks_passed:
        print("✓ All checks passed!")
        print("\nYou can now run performance tests:")
        print("  python scripts/run_performance_tests.py quick")
    else:
        print("✗ Some checks failed")
        print("\nPlease fix the issues above before running tests")
    print("="*70)
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())
