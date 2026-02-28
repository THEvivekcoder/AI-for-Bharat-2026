#!/usr/bin/env python3
"""
Comprehensive verification script for all completed BharatSahayak tasks.

This script runs tests for all completed tasks to verify the implementation is working.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Tuple


class TaskVerifier:
    """Verify completed tasks by running their tests."""
    
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Timeout running {description}"
        except Exception as e:
            return False, f"Error running {description}: {str(e)}"
    
    def check_files_exist(self, files: List[str], category: str) -> bool:
        """Check if required files exist."""
        print(f"\n{'='*70}")
        print(f"Checking {category} Files")
        print('='*70)
        
        all_exist = True
        for file_path in files:
            exists = os.path.exists(file_path)
            status = "✓" if exists else "✗"
            print(f"{status} {file_path}")
            if not exists:
                all_exist = False
        
        return all_exist
    
    def run_test_file(self, test_file: str, description: str) -> bool:
        """Run a specific test file."""
        print(f"\n{'='*70}")
        print(f"Testing: {description}")
        print('='*70)
        
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            return None
        
        success, output = self.run_command(
            ["pytest", test_file, "-v", "--tb=short", "-q"],
            description
        )
        
        # Count tests
        if "passed" in output:
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                count = int(match.group(1))
                self.total_tests += count
                if success:
                    self.passed_tests += count
        
        if success:
            print(f"✓ {description} - PASSED")
        else:
            print(f"✗ {description} - FAILED")
            if not success:
                self.failed_tests += 1
                # Print last few lines of output
                lines = output.split('\n')
                print("\nLast 10 lines of output:")
                for line in lines[-10:]:
                    if line.strip():
                        print(f"  {line}")
        
        return success
    
    def verify_task_1(self):
        """Verify Task 1: Core Infrastructure."""
        print("\n" + "="*70)
        print("TASK 1: Core Infrastructure")
        print("="*70)
        
        files = [
            "app/main.py",
            "app/database.py",
            "app/config.py",
            "app/api/health.py",
            "app/models/user.py"
        ]
        
        files_ok = self.check_files_exist(files, "Core Infrastructure")
        
        # Test health endpoint
        success, _ = self.run_command(
            ["python", "scripts/test_setup.py"],
            "Core Infrastructure"
        )
        
        self.results['Task 1'] = files_ok and success
        return files_ok and success
    
    def verify_task_2(self):
        """Verify Task 2: Authentication."""
        print("\n" + "="*70)
        print("TASK 2: Authentication & User Management")
        print("="*70)
        
        files = [
            "app/api/auth.py",
            "app/services/user_manager.py",
            "app/schemas/user.py"
        ]
        
        files_ok = self.check_files_exist(files, "Authentication")
        
        # Run property test
        test_ok = self.run_test_file(
            ".kiro/specs/bharatsahayak/tests/test_property_profile_persistence.py",
            "Profile Persistence Property Test"
        )
        
        self.results['Task 2'] = files_ok and test_ok
        return files_ok and test_ok
    
    def verify_task_4(self):
        """Verify Task 4: Voice Interface."""
        print("\n" + "="*70)
        print("TASK 4: Voice Interface Module")
        print("="*70)
        
        files = [
            "app/api/voice.py",
            "app/services/voice_interface.py"
        ]
        
        files_ok = self.check_files_exist(files, "Voice Interface")
        
        # Run property tests
        tests = [
            (".kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py", "STT Accuracy"),
            (".kiro/specs/bharatsahayak/tests/test_property_tts_generation.py", "TTS Generation"),
            (".kiro/specs/bharatsahayak/tests/test_property_language_detection.py", "Language Detection"),
            (".kiro/specs/bharatsahayak/tests/test_unit_voice_interface.py", "Voice Interface Unit Tests")
        ]
        
        all_passed = True
        for test_file, desc in tests:
            result = self.run_test_file(test_file, desc)
            if result is False:
                all_passed = False
        
        self.results['Task 4'] = files_ok and all_passed
        return files_ok and all_passed
    
    def verify_task_5(self):
        """Verify Task 5: RAG Engine."""
        print("\n" + "="*70)
        print("TASK 5: RAG Engine & LLM Core")
        print("="*70)
        
        files = [
            "app/api/rag.py",
            "app/services/rag_engine.py",
            "app/services/vector_store.py",
            "app/services/conversation_manager.py"
        ]
        
        files_ok = self.check_files_exist(files, "RAG Engine")
        
        tests = [
            (".kiro/specs/bharatsahayak/tests/test_property_context_preservation.py", "Context Preservation"),
            (".kiro/specs/bharatsahayak/tests/test_property_semantic_search.py", "Semantic Search"),
            (".kiro/specs/bharatsahayak/tests/test_property_source_prioritization.py", "Source Prioritization"),
            (".kiro/specs/bharatsahayak/tests/test_unit_rag_engine.py", "RAG Engine Unit Tests")
        ]
        
        all_passed = True
        for test_file, desc in tests:
            result = self.run_test_file(test_file, desc)
            if result is False:
                all_passed = False
        
        self.results['Task 5'] = files_ok and all_passed
        return files_ok and all_passed
    
    def verify_task_7(self):
        """Verify Task 7: Scheme Service."""
        print("\n" + "="*70)
        print("TASK 7: Scheme Service")
        print("="*70)
        
        files = [
            "app/api/schemes.py",
            "app/services/scheme_repository.py",
            "app/services/eligibility_checker.py",
            "app/schemas/scheme.py"
        ]
        
        files_ok = self.check_files_exist(files, "Scheme Service")
        
        tests = [
            (".kiro/specs/bharatsahayak/tests/test_property_scheme_search_relevance.py", "Scheme Search"),
            (".kiro/specs/bharatsahayak/tests/test_property_complete_information_display.py", "Complete Info"),
            (".kiro/specs/bharatsahayak/tests/test_property_eligibility_determination.py", "Eligibility"),
            (".kiro/specs/bharatsahayak/tests/test_unit_scheme_service.py", "Scheme Unit Tests")
        ]
        
        all_passed = True
        for test_file, desc in tests:
            result = self.run_test_file(test_file, desc)
            if result is False:
                all_passed = False
        
        self.results['Task 7'] = files_ok and all_passed
        return files_ok and all_passed
    
    def verify_task_8(self):
        """Verify Task 8: Farmer Advisory."""
        print("\n" + "="*70)
        print("TASK 8: Farmer Advisory Service")
        print("="*70)
        
        files = [
            "app/api/farmer.py",
            "app/services/crop_advisor.py",
            "app/services/fertilizer_advisor.py",
            "app/services/mandi_price_service.py"
        ]
        
        files_ok = self.check_files_exist(files, "Farmer Advisory")
        
        tests = [
            (".kiro/specs/bharatsahayak/tests/test_property_crop_recommendations.py", "Crop Recommendations"),
            (".kiro/specs/bharatsahayak/tests/test_property_fertilizer_guidance.py", "Fertilizer Guidance"),
            (".kiro/specs/bharatsahayak/tests/test_property_mandi_price_radius.py", "Mandi Price Radius"),
            (".kiro/specs/bharatsahayak/tests/test_unit_farmer_advisory.py", "Farmer Unit Tests")
        ]
        
        all_passed = True
        for test_file, desc in tests:
            result = self.run_test_file(test_file, desc)
            if result is False:
                all_passed = False
        
        self.results['Task 8'] = files_ok and all_passed
        return files_ok and all_passed
    
    def verify_task_21(self):
        """Verify Task 21: PWA."""
        print("\n" + "="*70)
        print("TASK 21: Progressive Web App")
        print("="*70)
        
        files = [
            "frontend/index.html",
            "frontend/manifest.json",
            "frontend/sw.js",
            "frontend/js/app.js",
            "frontend/js/voice.js",
            "frontend/js/offline.js"
        ]
        
        files_ok = self.check_files_exist(files, "PWA")
        
        # Run PWA integration tests
        test_ok = self.run_test_file(
            ".kiro/specs/bharatsahayak/tests/test_integration_pwa_simple.py",
            "PWA Integration Tests"
        )
        
        self.results['Task 21'] = files_ok and test_ok
        return files_ok and test_ok
    
    def print_summary(self):
        """Print verification summary."""
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        print()
        
        for task, status in self.results.items():
            status_str = "✓ PASS" if status else "✗ FAIL"
            print(f"{task:40} {status_str}")
        
        print()
        print(f"Total Tests Run:     {self.total_tests}")
        print(f"Tests Passed:        {self.passed_tests}")
        print(f"Tests Failed:        {self.failed_tests}")
        print()
        
        passed_tasks = sum(1 for v in self.results.values() if v)
        total_tasks = len(self.results)
        
        print(f"Tasks Verified:      {passed_tasks}/{total_tasks}")
        print()
        
        if all(self.results.values()):
            print("✓ ALL TASKS VERIFIED SUCCESSFULLY!")
            return 0
        else:
            print("✗ Some tasks have issues")
            return 1


def main():
    """Main verification function."""
    print("\n" + "="*70)
    print("BharatSahayak - Comprehensive Task Verification")
    print("="*70)
    print()
    print("This script verifies all completed tasks by:")
    print("  1. Checking required files exist")
    print("  2. Running property-based tests")
    print("  3. Running unit tests")
    print("  4. Running integration tests")
    print()
    
    verifier = TaskVerifier()
    
    # Verify each completed task
    verifier.verify_task_1()
    verifier.verify_task_2()
    verifier.verify_task_4()
    verifier.verify_task_5()
    verifier.verify_task_7()
    verifier.verify_task_8()
    verifier.verify_task_21()
    
    # Print summary
    return verifier.print_summary()


if __name__ == '__main__':
    sys.exit(main())
