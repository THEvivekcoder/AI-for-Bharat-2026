"""Integration tests for multilingual API responses."""

import json
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from src.api.schemes_search import lambda_handler as schemes_search_handler
from src.api.scheme_details import lambda_handler as scheme_details_handler
from src.api.check_eligibility import lambda_handler as check_eligibility_handler
from src.api.eligible_schemes import lambda_handler as eligible_schemes_handler
from src.models.scheme import Scheme, EligibilityCriteria


@pytest.fixture
def sample_scheme_with_translations():
    """Create a sample scheme with translations for testing."""
    return Scheme(
        scheme_id="PM-KISAN-2024",
        name="Pradhan Mantri Kisan Samman Nidhi",
        name_translations={
            "hi": "प्रधानमंत्री किसान सम्मान निधि",
            "ta": "பிரதம மந்திரி கிசான் சம்மான் நிதி",
            "te": "ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి",
            "bn": "প্রধানমন্ত্রী কিষাণ সম্মান নিধি"
        },
        category="agriculture",
        description="Income support scheme for farmers providing Rs. 6000 per year",
        description_translations={
            "hi": "किसानों के लिए आय सहायता योजना जो प्रति वर्ष 6000 रुपये प्रदान करती है",
            "ta": "விவசாயிகளுக்கு ஆண்டுக்கு ரூ. 6000 வருமான ஆதரவு திட்டம்",
            "te": "రైతులకు సంవత్సరానికి రూ. 6000 ఆదాయ మద్దతు పథకం",
            "bn": "কৃষকদের জন্য বছরে ৬০০০ টাকা আয় সহায়তা প্রকল্প"
        },
        benefits=["Rs. 6000 per year", "Direct bank transfer", "Three installments"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            occupation=["farmer"],
            income_max=500000
        ),
        required_documents=["Aadhaar", "Bank account", "Land records"],
        application_process=["Visit portal", "Fill form", "Submit documents"],
        application_url="https://pmkisan.gov.in",
        department="Ministry of Agriculture",
        state="",
        last_updated=datetime(2024, 10, 30, 0, 0),
        source_url="https://pmkisan.gov.in"
    )


@patch('src.api.scheme_details.scheme_repo')
def test_scheme_details_with_hindi_language(mock_repo, sample_scheme_with_translations):
    """Test scheme details API returns Hindi translations when lang=hi."""
    # Mock repository to return scheme with translations
    mock_repo.get.return_value = sample_scheme_with_translations
    
    # Create event with Hindi language parameter
    event = {
        'pathParameters': {'scheme_id': 'PM-KISAN-2024'},
        'queryStringParameters': {'lang': 'hi'}
    }
    
    # Call handler
    response = scheme_details_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Hindi translations are used
    assert body['name'] == "प्रधानमंत्री किसान सम्मान निधि"
    assert body['description'] == "किसानों के लिए आय सहायता योजना जो प्रति वर्ष 6000 रुपये प्रदान करती है"
    
    # Verify translations dict is still included
    assert 'name_translations' in body
    assert 'description_translations' in body


@patch('src.api.scheme_details.scheme_repo')
def test_scheme_details_with_tamil_language(mock_repo, sample_scheme_with_translations):
    """Test scheme details API returns Tamil translations when lang=ta."""
    mock_repo.get.return_value = sample_scheme_with_translations
    
    event = {
        'pathParameters': {'scheme_id': 'PM-KISAN-2024'},
        'queryStringParameters': {'lang': 'ta'}
    }
    
    response = scheme_details_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Tamil translations are used
    assert body['name'] == "பிரதம மந்திரி கிசான் சம்மான் நிதி"
    assert body['description'] == "விவசாயிகளுக்கு ஆண்டுக்கு ரூ. 6000 வருமான ஆதரவு திட்டம்"


@patch('src.api.scheme_details.scheme_repo')
def test_scheme_details_fallback_to_english(mock_repo, sample_scheme_with_translations):
    """Test scheme details API falls back to English when translation unavailable."""
    mock_repo.get.return_value = sample_scheme_with_translations
    
    # Request unsupported language
    event = {
        'pathParameters': {'scheme_id': 'PM-KISAN-2024'},
        'queryStringParameters': {'lang': 'mr'}  # Marathi not in translations
    }
    
    response = scheme_details_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify English is used as fallback
    assert body['name'] == "Pradhan Mantri Kisan Samman Nidhi"
    assert body['description'] == "Income support scheme for farmers providing Rs. 6000 per year"


@patch('src.api.scheme_details.scheme_repo')
def test_scheme_details_default_english(mock_repo, sample_scheme_with_translations):
    """Test scheme details API defaults to English when no lang parameter."""
    mock_repo.get.return_value = sample_scheme_with_translations
    
    event = {
        'pathParameters': {'scheme_id': 'PM-KISAN-2024'},
        'queryStringParameters': None  # No language parameter
    }
    
    response = scheme_details_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify English is used by default
    assert body['name'] == "Pradhan Mantri Kisan Samman Nidhi"
    assert body['description'] == "Income support scheme for farmers providing Rs. 6000 per year"


@patch('src.api.schemes_search.scheme_repo')
def test_schemes_search_with_bengali_language(mock_repo, sample_scheme_with_translations):
    """Test schemes search API returns Bengali translations when lang=bn."""
    mock_repo.search_schemes.return_value = [sample_scheme_with_translations]
    
    event = {
        'queryStringParameters': {
            'q': 'farmer',
            'lang': 'bn'
        }
    }
    
    response = schemes_search_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Bengali translations are used in search results
    assert len(body['schemes']) == 1
    scheme = body['schemes'][0]
    assert scheme['name'] == "প্রধানমন্ত্রী কিষাণ সম্মান নিধি"
    assert scheme['description'] == "কৃষকদের জন্য বছরে ৬০০০ টাকা আয় সহায়তা প্রকল্প"


@patch('src.api.schemes_search.scheme_repo')
def test_schemes_search_with_telugu_language(mock_repo, sample_scheme_with_translations):
    """Test schemes search API returns Telugu translations when lang=te."""
    mock_repo.search_schemes.return_value = [sample_scheme_with_translations]
    
    event = {
        'queryStringParameters': {
            'category': 'agriculture',
            'lang': 'te'
        }
    }
    
    response = schemes_search_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Telugu translations are used
    scheme = body['schemes'][0]
    assert scheme['name'] == "ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి"
    assert scheme['description'] == "రైతులకు సంవత్సరానికి రూ. 6000 ఆదాయ మద్దతు పథకం"


@patch('src.api.schemes_search.scheme_repo')
def test_schemes_search_fallback_to_english(mock_repo, sample_scheme_with_translations):
    """Test schemes search API falls back to English when translation unavailable."""
    mock_repo.search_schemes.return_value = [sample_scheme_with_translations]
    
    event = {
        'queryStringParameters': {
            'q': 'farmer',
            'lang': 'gu'  # Gujarati not in translations
        }
    }
    
    response = schemes_search_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify English is used as fallback
    scheme = body['schemes'][0]
    assert scheme['name'] == "Pradhan Mantri Kisan Samman Nidhi"
    assert scheme['description'] == "Income support scheme for farmers providing Rs. 6000 per year"


@patch('src.api.eligible_schemes.scheme_repo')
@patch('src.api.eligible_schemes.eligibility_checker')
def test_eligible_schemes_with_hindi_language(mock_checker, mock_repo, sample_scheme_with_translations):
    """Test eligible schemes API returns Hindi translations when user language is Hindi."""
    from src.core.eligibility_checker import EligibilityResult
    
    # Mock repository and eligibility checker
    mock_repo.get_all_schemes.return_value = [sample_scheme_with_translations]
    mock_checker.check_eligibility.return_value = EligibilityResult(
        is_eligible=True,
        reasoning=["Age meets requirement", "Occupation matches"],
        missing_criteria=[],
        confidence=1.0
    )
    
    # Create request with Hindi-speaking user
    event = {
        'body': json.dumps({
            'user_profile': {
                'user_id': 'user_123',
                'phone_number': '+919876543210',
                'language': 'hi',  # User prefers Hindi
                'location': {
                    'state': 'Maharashtra',
                    'district': 'Pune',
                    'pincode': '411014'
                },
                'age': 35,
                'gender': 'male',
                'education_level': 'secondary',
                'occupation': 'farmer',
                'income_bracket': '100000-300000',
                'preferences': {
                    'preferred_categories': ['agriculture']
                }
            }
        })
    }
    
    response = eligible_schemes_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Hindi translations are used for eligible schemes
    assert len(body['eligible_schemes']) == 1
    scheme = body['eligible_schemes'][0]
    assert scheme['name'] == "प्रधानमंत्री किसान सम्मान निधि"
    assert scheme['description'] == "किसानों के लिए आय सहायता योजना जो प्रति वर्ष 6000 रुपये प्रदान करती है"
    
    # Verify translations dict is included
    assert 'name_translations' in scheme
    assert 'description_translations' in scheme


@patch('src.api.eligible_schemes.scheme_repo')
@patch('src.api.eligible_schemes.eligibility_checker')
def test_eligible_schemes_fallback_to_english(mock_checker, mock_repo, sample_scheme_with_translations):
    """Test eligible schemes API falls back to English when translation unavailable."""
    from src.core.eligibility_checker import EligibilityResult
    
    mock_repo.get_all_schemes.return_value = [sample_scheme_with_translations]
    mock_checker.check_eligibility.return_value = EligibilityResult(
        is_eligible=True,
        reasoning=["Eligible"],
        missing_criteria=[],
        confidence=1.0
    )
    
    # User with unsupported language
    event = {
        'body': json.dumps({
            'user_profile': {
                'user_id': 'user_123',
                'phone_number': '+919876543210',
                'language': 'ml',  # Malayalam not in translations
                'location': {
                    'state': 'Kerala',
                    'district': 'Kochi',
                    'pincode': '682001'
                },
                'age': 40,
                'occupation': 'farmer',
                'preferences': {
                    'preferred_categories': []
                }
            }
        })
    }
    
    response = eligible_schemes_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify English is used as fallback
    scheme = body['eligible_schemes'][0]
    assert scheme['name'] == "Pradhan Mantri Kisan Samman Nidhi"
    assert scheme['description'] == "Income support scheme for farmers providing Rs. 6000 per year"



@patch('src.api.check_eligibility.scheme_repo')
@patch('src.api.check_eligibility.eligibility_checker')
def test_check_eligibility_with_language_parameter(mock_checker, mock_repo, sample_scheme_with_translations):
    """Test check eligibility API returns translated scheme name when language specified."""
    from src.api.check_eligibility import lambda_handler as check_eligibility_handler
    from src.core.eligibility_checker import EligibilityResult
    
    # Mock repository and eligibility checker
    mock_repo.get.return_value = sample_scheme_with_translations
    mock_checker.check_eligibility.return_value = EligibilityResult(
        is_eligible=True,
        reasoning=["Age meets requirement", "Occupation matches"],
        missing_criteria=[],
        confidence=1.0
    )
    
    # Create request with Hindi language
    event = {
        'body': json.dumps({
            'scheme_id': 'PM-KISAN-2024',
            'language': 'hi',
            'user_profile': {
                'user_id': 'user_123',
                'phone_number': '+919876543210',
                'language': 'hi',
                'location': {
                    'state': 'Maharashtra',
                    'district': 'Pune',
                    'pincode': '411014'
                },
                'age': 35,
                'gender': 'male',
                'occupation': 'farmer',
                'preferences': {
                    'preferred_categories': []
                }
            }
        })
    }
    
    response = check_eligibility_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify Hindi scheme name is returned
    assert body['scheme_name'] == "प्रधानमंत्री किसान सम्मान निधि"
    assert body['is_eligible'] is True


@patch('src.api.check_eligibility.scheme_repo')
@patch('src.api.check_eligibility.eligibility_checker')
def test_check_eligibility_fallback_to_english(mock_checker, mock_repo, sample_scheme_with_translations):
    """Test check eligibility API falls back to English when translation unavailable."""
    from src.api.check_eligibility import lambda_handler as check_eligibility_handler
    from src.core.eligibility_checker import EligibilityResult
    
    mock_repo.get.return_value = sample_scheme_with_translations
    mock_checker.check_eligibility.return_value = EligibilityResult(
        is_eligible=False,
        reasoning=["Age requirement not met"],
        missing_criteria=["age"],
        confidence=1.0
    )
    
    # Request with unsupported language
    event = {
        'body': json.dumps({
            'scheme_id': 'PM-KISAN-2024',
            'language': 'pa',  # Punjabi not in translations
            'user_profile': {
                'user_id': 'user_456',
                'phone_number': '+919876543211',
                'language': 'pa',
                'location': {
                    'state': 'Punjab',
                    'district': 'Ludhiana',
                    'pincode': '141001'
                },
                'age': 15,
                'occupation': 'student',
                'preferences': {
                    'preferred_categories': []
                }
            }
        })
    }
    
    response = check_eligibility_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify English is used as fallback
    assert body['scheme_name'] == "Pradhan Mantri Kisan Samman Nidhi"
    assert body['is_eligible'] is False
