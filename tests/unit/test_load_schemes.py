"""Unit tests for scheme data loader script."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add infrastructure/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infrastructure" / "scripts"))

from load_schemes import (
    get_sample_schemes,
    validate_scheme,
    load_from_json,
)


class TestSampleSchemes:
    """Test sample scheme generation."""
    
    def test_get_sample_schemes_returns_list(self):
        """Test that get_sample_schemes returns a list."""
        schemes = get_sample_schemes()
        assert isinstance(schemes, list)
        assert len(schemes) >= 20, "Should have at least 20 sample schemes"
    
    def test_sample_schemes_have_required_fields(self):
        """Test that all sample schemes have required fields."""
        schemes = get_sample_schemes()
        required_fields = [
            'scheme_id', 'name', 'category', 'description',
            'benefits', 'eligibility_criteria', 'required_documents',
            'application_process', 'department', 'last_updated', 'source_url'
        ]
        
        for scheme in schemes:
            for field in required_fields:
                assert field in scheme, f"Scheme {scheme.get('scheme_id')} missing field: {field}"
    
    def test_sample_schemes_cover_all_categories(self):
        """Test that sample schemes cover all required categories."""
        schemes = get_sample_schemes()
        categories = {scheme['category'] for scheme in schemes}
        
        expected_categories = {
            'agriculture', 'health', 'education', 'employment', 'social_welfare'
        }
        
        assert categories == expected_categories, f"Missing categories: {expected_categories - categories}"
    
    def test_sample_schemes_have_unique_ids(self):
        """Test that all scheme IDs are unique."""
        schemes = get_sample_schemes()
        scheme_ids = [scheme['scheme_id'] for scheme in schemes]
        
        assert len(scheme_ids) == len(set(scheme_ids)), "Duplicate scheme IDs found"
    
    def test_sample_schemes_eligibility_criteria_structure(self):
        """Test that eligibility criteria have correct structure."""
        schemes = get_sample_schemes()
        
        for scheme in schemes:
            eligibility = scheme['eligibility_criteria']
            assert isinstance(eligibility, dict), f"Eligibility criteria must be dict for {scheme['scheme_id']}"
            
            # Check that custom_criteria exists
            assert 'custom_criteria' in eligibility


class TestSchemeValidation:
    """Test scheme validation."""
    
    def test_validate_valid_scheme(self):
        """Test validation of a valid scheme."""
        schemes = get_sample_schemes()
        assert len(schemes) > 0, "No sample schemes available"
        
        # Test first scheme
        result = validate_scheme(schemes[0])
        assert result is True
    
    def test_validate_all_sample_schemes(self):
        """Test that all sample schemes are valid."""
        schemes = get_sample_schemes()
        
        for scheme in schemes:
            result = validate_scheme(scheme)
            assert result is True, f"Scheme {scheme['scheme_id']} failed validation"
    
    def test_validate_scheme_with_missing_required_field(self):
        """Test validation fails for scheme missing required field."""
        invalid_scheme = {
            'scheme_id': 'TEST-001',
            'name': 'Test Scheme',
            # Missing category
            'description': 'Test description',
            'eligibility_criteria': {},
            'department': 'Test Dept',
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'source_url': 'https://example.com'
        }
        
        result = validate_scheme(invalid_scheme)
        assert result is False
    
    def test_validate_scheme_with_invalid_eligibility(self):
        """Test validation fails for invalid eligibility criteria."""
        invalid_scheme = {
            'scheme_id': 'TEST-002',
            'name': 'Test Scheme',
            'category': 'agriculture',
            'description': 'Test description',
            'eligibility_criteria': {
                'age_min': 200,  # Invalid age
            },
            'department': 'Test Dept',
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'source_url': 'https://example.com'
        }
        
        result = validate_scheme(invalid_scheme)
        assert result is False


class TestJSONLoader:
    """Test JSON file loading."""
    
    def test_load_from_json_single_scheme(self, tmp_path):
        """Test loading a single scheme from JSON."""
        # Create temporary JSON file
        scheme_data = {
            'scheme_id': 'TEST-JSON-001',
            'name': 'Test JSON Scheme',
            'category': 'agriculture',
            'description': 'Test description',
            'eligibility_criteria': {},
            'department': 'Test Dept',
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'source_url': 'https://example.com'
        }
        
        json_file = tmp_path / "test_scheme.json"
        json_file.write_text(json.dumps(scheme_data))
        
        # Load from JSON
        schemes = load_from_json(str(json_file))
        
        assert len(schemes) == 1
        assert schemes[0]['scheme_id'] == 'TEST-JSON-001'
    
    def test_load_from_json_multiple_schemes(self, tmp_path):
        """Test loading multiple schemes from JSON array."""
        # Create temporary JSON file with array
        schemes_data = [
            {
                'scheme_id': 'TEST-JSON-001',
                'name': 'Test Scheme 1',
                'category': 'agriculture',
                'description': 'Test description 1',
                'eligibility_criteria': {},
                'department': 'Test Dept',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'source_url': 'https://example.com'
            },
            {
                'scheme_id': 'TEST-JSON-002',
                'name': 'Test Scheme 2',
                'category': 'health',
                'description': 'Test description 2',
                'eligibility_criteria': {},
                'department': 'Test Dept',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'source_url': 'https://example.com'
            }
        ]
        
        json_file = tmp_path / "test_schemes.json"
        json_file.write_text(json.dumps(schemes_data))
        
        # Load from JSON
        schemes = load_from_json(str(json_file))
        
        assert len(schemes) == 2
        assert schemes[0]['scheme_id'] == 'TEST-JSON-001'
        assert schemes[1]['scheme_id'] == 'TEST-JSON-002'


class TestCategoryDistribution:
    """Test category distribution in sample schemes."""
    
    def test_each_category_has_multiple_schemes(self):
        """Test that each category has at least 3 schemes."""
        schemes = get_sample_schemes()
        category_counts = {}
        
        for scheme in schemes:
            category = scheme['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            assert count >= 3, f"Category {category} has only {count} schemes, expected at least 3"
    
    def test_schemes_have_translations(self):
        """Test that schemes have Hindi translations."""
        schemes = get_sample_schemes()
        
        schemes_with_translations = 0
        for scheme in schemes:
            if scheme.get('name_translations') and 'hi' in scheme['name_translations']:
                schemes_with_translations += 1
        
        # At least 80% of schemes should have translations
        assert schemes_with_translations >= len(schemes) * 0.8, \
            f"Only {schemes_with_translations}/{len(schemes)} schemes have Hindi translations"
