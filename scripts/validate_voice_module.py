"""
Validation script for voice interface module structure

This script validates the module structure without requiring
heavy dependencies to be installed.
"""

import sys
import os
import ast

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validate_file_structure():
    """Validate that all required files exist"""
    print("Validating file structure...")
    
    required_files = [
        "app/services/voice_interface.py",
        "app/api/voice.py",
        "app/schemas/voice.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} missing")
            all_exist = False
    
    return all_exist


def validate_python_syntax(file_path):
    """Validate Python syntax of a file"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error in {file_path}: {e}")
        return False


def validate_syntax():
    """Validate Python syntax of all files"""
    print("\nValidating Python syntax...")
    
    files = [
        "app/services/voice_interface.py",
        "app/api/voice.py",
        "app/schemas/voice.py",
    ]
    
    all_valid = True
    for file_path in files:
        if validate_python_syntax(file_path):
            print(f"  ✓ {file_path} syntax valid")
        else:
            all_valid = False
    
    return all_valid


def validate_class_definitions():
    """Validate that required classes are defined"""
    print("\nValidating class definitions...")
    
    try:
        with open("app/services/voice_interface.py", 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        required_classes = [
            "SpeechToTextEngine",
            "TextToSpeechEngine",
            "TranscriptionResult",
            "AudioProcessingConfig",
            "SupportedLanguage"
        ]
        
        defined_classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        all_defined = True
        for cls in required_classes:
            if cls in defined_classes:
                print(f"  ✓ {cls} defined")
            else:
                print(f"  ✗ {cls} missing")
                all_defined = False
        
        return all_defined
        
    except Exception as e:
        print(f"  ✗ Error validating classes: {e}")
        return False


def validate_api_endpoints():
    """Validate that required API endpoints are defined"""
    print("\nValidating API endpoints...")
    
    try:
        with open("app/api/voice.py", 'r') as f:
            code = f.read()
        
        required_endpoints = [
            "voice_to_text",
            "text_to_voice",
            "get_supported_languages"
        ]
        
        all_defined = True
        for endpoint in required_endpoints:
            if f"def {endpoint}" in code or f"async def {endpoint}" in code:
                print(f"  ✓ {endpoint} endpoint defined")
            else:
                print(f"  ✗ {endpoint} endpoint missing")
                all_defined = False
        
        return all_defined
        
    except Exception as e:
        print(f"  ✗ Error validating endpoints: {e}")
        return False


def validate_schemas():
    """Validate that required schemas are defined"""
    print("\nValidating Pydantic schemas...")
    
    try:
        with open("app/schemas/voice.py", 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        required_schemas = [
            "TranscriptionResponse",
            "TextToSpeechRequest",
            "SupportedLanguagesResponse",
            "LanguageInfo",
            "VoiceErrorResponse"
        ]
        
        defined_classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        all_defined = True
        for schema in required_schemas:
            if schema in defined_classes:
                print(f"  ✓ {schema} schema defined")
            else:
                print(f"  ✗ {schema} schema missing")
                all_defined = False
        
        return all_defined
        
    except Exception as e:
        print(f"  ✗ Error validating schemas: {e}")
        return False


def validate_router_registration():
    """Validate that voice router is registered in main.py"""
    print("\nValidating router registration...")
    
    try:
        with open("app/main.py", 'r') as f:
            code = f.read()
        
        checks = [
            ("voice router import", "from app.api.voice import router as voice_router"),
            ("voice router included", "app.include_router(voice_router")
        ]
        
        all_registered = True
        for check_name, check_string in checks:
            if check_string in code:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} missing")
                all_registered = False
        
        return all_registered
        
    except Exception as e:
        print(f"  ✗ Error validating router registration: {e}")
        return False


def main():
    """Run all validations"""
    print("=" * 60)
    print("Voice Interface Module Validation")
    print("=" * 60)
    
    results = []
    
    # Run validations
    results.append(("File Structure", validate_file_structure()))
    results.append(("Python Syntax", validate_syntax()))
    results.append(("Class Definitions", validate_class_definitions()))
    results.append(("API Endpoints", validate_api_endpoints()))
    results.append(("Pydantic Schemas", validate_schemas()))
    results.append(("Router Registration", validate_router_registration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✓ All validations passed!")
        print("\nNote: To fully test the voice interface, install dependencies:")
        print("  pip install -r requirements.txt")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
