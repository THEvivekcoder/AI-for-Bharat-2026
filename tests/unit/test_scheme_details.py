"""Unit tests for scheme details Lambda function."""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.api.scheme_details import lambda_handler
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.core.scheme_repository import ItemNotFoundError, DynamoDBRepositoryError


@pytest.fixture
def sample_scheme():
    """Create a sample scheme for testing."""
    return Scheme(
        scheme_id="PM-KISAN-2024",
        name="Pradhan Mantri Kisan Samman Nidhi",
        name_translations={
            "hi": "प्रधानमंत्री किसान सम्मान निधि",
            "mr": "प्रधानमंत्री किसान सन्मान निधी"
        },
        category="agriculture",
        description="Income support scheme for farmers providing Rs. 6000 per year in three installments",
        description_translations={
            "hi": "किसानों के लिए आय सहायता योजना जो तीन किस्तों में प्रति वर्ष 6000 रुपये प्रदान करती है"
        },
        benefits=[
            "Rs. 2000 per installment (3 times per year)",
            "Direct bank transfer",
            "No intermediaries"
        ],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            occupation=["farmer"],
            custom_criteria={
                "land_ownership": "yes",
                "cultivable_land": "any"
            }
        ),
        required_documents=[
            "Aadhaar card",
            "Bank account details",
            "Land ownership documents"
        ],
        application_process=[
            "Visit PM-KISAN portal or nearest CSC",
            "Fill registration form with Aadhaar and bank details",
            "Upload land records",
            "Submit application",
            "Receive confirmation SMS"
        ],
        application_url="https://pmkisan.gov.in",
        department="Ministry of Agriculture and Farmers Welfare",
        state=None,
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url="https://pmkisan.gov.in"
    )


@pytest.fixture
def mock_scheme_repo():
    """Create a mock scheme repository."""
    with patch('src.api.scheme_details.scheme_repo') as mock_repo:
        yield mock_repo


def test_get_scheme_details_success(mock_scheme_repo, sample_scheme):
    """Test successful retrieval of scheme details."""
    # Arrange
    mock_scheme_repo.get.return_value = sample_scheme
    event = {
        'pathParameters': {
            'scheme_id': 'PM-KISAN-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 200
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert body['scheme_id'] == 'PM-KISAN-2024'
    assert body['name'] == 'Pradhan Mantri Kisan Samman Nidhi'
    assert body['category'] == 'agriculture'
    assert body['description'] == 'Income support scheme for farmers providing Rs. 6000 per year in three installments'
    
    # Verify all required fields are present
    assert 'name_translations' in body
    assert 'description_translations' in body
    assert 'benefits' in body
    assert 'eligibility_criteria' in body
    assert 'required_documents' in body
    assert 'application_process' in body
    assert 'application_url' in body
    assert 'department' in body
    assert 'state' in body
    assert 'last_updated' in body
    assert 'source_url' in body
    
    # Verify translations are included
    assert body['name_translations']['hi'] == 'प्रधानमंत्री किसान सम्मान निधि'
    assert body['description_translations']['hi'] == 'किसानों के लिए आय सहायता योजना जो तीन किस्तों में प्रति वर्ष 6000 रुपये प्रदान करती है'
    
    # Verify benefits list
    assert len(body['benefits']) == 3
    assert 'Rs. 2000 per installment (3 times per year)' in body['benefits']
    
    # Verify eligibility criteria
    assert body['eligibility_criteria']['age_min'] == 18
    assert body['eligibility_criteria']['occupation'] == ['farmer']
    assert body['eligibility_criteria']['custom_criteria']['land_ownership'] == 'yes'
    
    # Verify required documents
    assert len(body['required_documents']) == 3
    assert 'Aadhaar card' in body['required_documents']
    assert 'Bank account details' in body['required_documents']
    assert 'Land ownership documents' in body['required_documents']
    
    # Verify application process
    assert len(body['application_process']) == 5
    assert 'Visit PM-KISAN portal or nearest CSC' in body['application_process']
    assert 'Receive confirmation SMS' in body['application_process']
    
    # Verify other fields
    assert body['application_url'] == 'https://pmkisan.gov.in'
    assert body['department'] == 'Ministry of Agriculture and Farmers Welfare'
    assert body['state'] is None
    assert body['source_url'] == 'https://pmkisan.gov.in'
    
    # Verify repository was called correctly
    mock_scheme_repo.get.assert_called_once_with('PM-KISAN-2024')


def test_get_scheme_details_not_found(mock_scheme_repo):
    """Test retrieval of non-existent scheme."""
    # Arrange
    mock_scheme_repo.get.side_effect = ItemNotFoundError("Scheme not found")
    event = {
        'pathParameters': {
            'scheme_id': 'NON-EXISTENT'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'not found' in body['error'].lower()


def test_get_scheme_details_missing_scheme_id(mock_scheme_repo):
    """Test request with missing scheme_id parameter."""
    # Arrange
    event = {
        'pathParameters': {}
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'missing' in body['error'].lower()
    
    # Verify repository was not called
    mock_scheme_repo.get.assert_not_called()


def test_get_scheme_details_empty_scheme_id(mock_scheme_repo):
    """Test request with empty scheme_id parameter."""
    # Arrange
    event = {
        'pathParameters': {
            'scheme_id': '   '
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'invalid' in body['error'].lower()
    
    # Verify repository was not called
    mock_scheme_repo.get.assert_not_called()


def test_get_scheme_details_no_path_parameters(mock_scheme_repo):
    """Test request with no pathParameters key."""
    # Arrange
    event = {}
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


def test_get_scheme_details_database_error(mock_scheme_repo):
    """Test handling of database errors."""
    # Arrange
    mock_scheme_repo.get.side_effect = DynamoDBRepositoryError("Database connection failed")
    event = {
        'pathParameters': {
            'scheme_id': 'PM-KISAN-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'failed' in body['error'].lower()


def test_get_scheme_details_unexpected_error(mock_scheme_repo):
    """Test handling of unexpected errors."""
    # Arrange
    mock_scheme_repo.get.side_effect = Exception("Unexpected error")
    event = {
        'pathParameters': {
            'scheme_id': 'PM-KISAN-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body


def test_get_scheme_details_state_specific_scheme(mock_scheme_repo):
    """Test retrieval of state-specific scheme."""
    # Arrange
    state_scheme = Scheme(
        scheme_id="MH-FARMER-2024",
        name="Maharashtra Farmer Support Scheme",
        name_translations={"mr": "महाराष्ट्र शेतकरी सहाय्य योजना"},
        category="agriculture",
        description="State-level farmer support scheme",
        description_translations={"mr": "राज्य स्तरीय शेतकरी सहाय्य योजना"},
        benefits=["Financial assistance", "Crop insurance"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            occupation=["farmer"],
            location=["Maharashtra"]
        ),
        required_documents=["Aadhaar", "Land records"],
        application_process=["Visit district office", "Submit application"],
        application_url="https://maharashtra.gov.in/farmer-scheme",
        department="Maharashtra Agriculture Department",
        state="Maharashtra",
        last_updated=datetime(2024, 1, 20, 12, 0, 0),
        source_url="https://maharashtra.gov.in"
    )
    mock_scheme_repo.get.return_value = state_scheme
    event = {
        'pathParameters': {
            'scheme_id': 'MH-FARMER-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['state'] == 'Maharashtra'
    assert body['department'] == 'Maharashtra Agriculture Department'


def test_get_scheme_details_cors_headers(mock_scheme_repo, sample_scheme):
    """Test that CORS headers are included in response."""
    # Arrange
    mock_scheme_repo.get.return_value = sample_scheme
    event = {
        'pathParameters': {
            'scheme_id': 'PM-KISAN-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert 'headers' in response
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert response['headers']['Content-Type'] == 'application/json'


def test_get_scheme_details_complete_eligibility_criteria(mock_scheme_repo):
    """Test that complete eligibility criteria with all conditions are returned."""
    # Arrange
    complex_scheme = Scheme(
        scheme_id="COMPLEX-SCHEME-2024",
        name="Complex Eligibility Scheme",
        name_translations={},
        category="social_welfare",
        description="Scheme with complex eligibility criteria",
        description_translations={},
        benefits=["Benefit 1", "Benefit 2"],
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=60,
            income_max=500000,
            gender="female",
            occupation=["farmer", "laborer"],
            education=["primary", "secondary"],
            location=["Rural"],
            caste=["SC", "ST", "OBC"],
            custom_criteria={
                "bpl_card": "yes",
                "disability": "any",
                "widow": "yes"
            }
        ),
        required_documents=["Aadhaar", "Income certificate", "Caste certificate"],
        application_process=["Step 1", "Step 2"],
        application_url="https://example.gov.in",
        department="Social Welfare Department",
        state="Uttar Pradesh",
        last_updated=datetime(2024, 1, 25, 14, 0, 0),
        source_url="https://example.gov.in"
    )
    mock_scheme_repo.get.return_value = complex_scheme
    event = {
        'pathParameters': {
            'scheme_id': 'COMPLEX-SCHEME-2024'
        }
    }
    
    # Act
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify all eligibility criteria fields are present
    criteria = body['eligibility_criteria']
    assert criteria['age_min'] == 18
    assert criteria['age_max'] == 60
    assert criteria['income_max'] == 500000
    assert criteria['gender'] == 'female'
    assert criteria['occupation'] == ['farmer', 'laborer']
    assert criteria['education'] == ['primary', 'secondary']
    assert criteria['location'] == ['Rural']
    assert criteria['caste'] == ['SC', 'ST', 'OBC']
    assert criteria['custom_criteria']['bpl_card'] == 'yes'
    assert criteria['custom_criteria']['disability'] == 'any'
    assert criteria['custom_criteria']['widow'] == 'yes'
