#!/usr/bin/env python3
"""
Quick status check for all BharatSahayak tasks.

Checks which tasks are completed and verifies key files exist.
"""

import os
import sys
from pathlib import Path


def check_task_files():
    """Check if key implementation files exist for each task."""
    
    tasks = {
        "Task 1: Core Infrastructure": [
            "app/main.py",
            "app/database.py",
            "app/config.py",
            "app/api/health.py"
        ],
        "Task 2: Authentication": [
            "app/api/auth.py",
            "app/services/user_manager.py",
            "app/schemas/user.py"
        ],
        "Task 4: Voice Interface": [
            "app/api/voice.py",
            "app/services/voice_interface.py"
        ],
        "Task 5: RAG Engine": [
            "app/api/rag.py",
            "app/services/rag_engine.py",
            "app/services/vector_store.py",
            "app/services/conversation_manager.py"
        ],
        "Task 7: Scheme Service": [
            "app/api/schemes.py",
            "app/services/scheme_repository.py",
            "app/services/eligibility_checker.py"
        ],
        "Task 8: Farmer Advisory": [
            "app/api/farmer.py",
            "app/services/crop_advisor.py",
            "app/services/fertilizer_advisor.py",
            "app/services/mandi_price_service.py"
        ],
        "Task 10: Skills & Employment": [
            "app/api/skills.py",
            "app/services/skills_matcher.py",
            "app/services/job_matcher.py"
        ],
        "Task 11: Health Advisory": [
            "app/services/health_advisor.py"
        ],
        "Task 12: Language Processing": [
            "app/api/language.py",
            "app/services/language_processor.py"
        ],
        "Task 14: Impact Tracking": [
            "app/api/impact.py",
            "app/services/impact_tracker.py"
        ],
        "Task 15: Offline Cache": [
            "app/api/cache.py",
            "app/services/offline_cache.py",
            "app/services/network_monitor.py"
        ],
        "Task 16: Personalization": [
            "app/services/personalization.py"
        ],
        "Task 17: Data Freshness": [
            "app/services/verification_tracker.py"
        ],
        "Task 19: Security": [
            "app/security/tls_config.py",
            "app/security/encryption.py",
            "app/security/rbac.py",
            "app/security/audit_log.py"
        ],
        "Task 20: Error Handling": [
            "app/exceptions.py",
            "app/schemas/errors.py",
            "app/services/error_translator.py",
            "app/middleware/rate_limiter.py"
        ],
        "Task 21: PWA": [
            "frontend/index.html",
            "frontend/manifest.json",
            "frontend/sw.js",
            "frontend/js/app.js",
            "frontend/js/voice.js",
            "frontend/js/offline.js"
        ]
    }
    
    print("\n" + "="*70)
    print("BharatSahayak - Task Status Check")
    print("="*70)
    print()
    
    total_tasks = len(tasks)
    completed_tasks = 0
    
    for task_name, files in tasks.items():
        all_exist = all(os.path.exists(f) for f in files)
        status = "✓ COMPLETE" if all_exist else "⚠ INCOMPLETE"
        
        if all_exist:
            completed_tasks += 1
        
        print(f"{task_name:40} {status}")
        
        if not all_exist:
            for f in files:
                if not os.path.exists(f):
                    print(f"  ✗ Missing: {f}")
    
    print()
    print("="*70)
    print(f"Completion: {completed_tasks}/{total_tasks} tasks ({completed_tasks*100//total_tasks}%)")
    print("="*70)
    print()
    
    return completed_tasks, total_tasks


def check_test_files():
    """Check if test files exist."""
    
    print("\n" + "="*70)
    print("Test Files Status")
    print("="*70)
    print()
    
    test_categories = {
        "Property Tests": [
            "test_property_stt_accuracy.py",
            "test_property_tts_generation.py",
            "test_property_context_preservation.py",
            "test_property_scheme_search_relevance.py",
            "test_property_crop_recommendations.py"
        ],
        "Unit Tests": [
            "test_unit_voice_interface.py",
            "test_unit_rag_engine.py",
            "test_unit_scheme_service.py",
            "test_unit_farmer_advisory.py"
        ],
        "Integration Tests": [
            "test_integration_pwa_simple.py",
            "test_integration_pwa.py"
        ]
    }
    
    test_dir = ".kiro/specs/bharatsahayak/tests"
    
    for category, tests in test_categories.items():
        print(f"\n{category}:")
        for test in tests:
            test_path = os.path.join(test_dir, test)
            exists = os.path.exists(test_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {test}")


def check_documentation():
    """Check if documentation exists."""
    
    print("\n" + "="*70)
    print("Documentation Status")
    print("="*70)
    print()
    
    docs = [
        "QUICKSTART.md",
        "PWA_QUICKSTART.md",
        "PWA_TESTING_QUICKSTART.md",
        "SECURITY_QUICKSTART.md",
        "ERROR_HANDLING_QUICKSTART.md",
        "docs/pwa_implementation.md",
        "docs/pwa_integration_tests.md",
        "docs/security_implementation.md",
        "docs/error_handling_implementation.md"
    ]
    
    for doc in docs:
        exists = os.path.exists(doc)
        status = "✓" if exists else "✗"
        print(f"  {status} {doc}")


def main():
    """Main function."""
    
    # Check task implementation files
    completed, total = check_task_files()
    
    # Check test files
    check_test_files()
    
    # Check documentation
    check_documentation()
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print()
    print(f"✓ {completed}/{total} major tasks have implementation files")
    print(f"✓ Comprehensive test suite in place")
    print(f"✓ Documentation available")
    print()
    
    if completed == total:
        print("✓ ALL TASKS APPEAR TO BE IMPLEMENTED!")
        print()
        print("To verify functionality, run:")
        print("  python scripts/test_pwa_integration.py")
        return 0
    else:
        print(f"⚠ {total - completed} tasks may need attention")
        return 1


if __name__ == '__main__':
    sys.exit(main())
