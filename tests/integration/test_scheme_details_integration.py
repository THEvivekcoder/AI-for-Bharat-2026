"""Integration tests for scheme details Lambda function with DynamoDB."""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from decimal import Decimal

from src.api.scheme_details import lambda_handler
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = MagicMock()
    return table


@pytest.fixture
def sample_scheme_item():
    """Create a sample DynamoDB scheme item."""
    return {
        'scheme_id': 'PM-KISAN-2024',
        'name': 'Pradhan Mantri Kisan Samman Nidhi',
        'name_translations': {
            'hi': 'प्रधानमंत्री किसान सम्मान निधि',
            'mr': 'प्रधानमंत्री किसान सन्मान निधी'
        },
        'category': 'agriculture',
        'description': 'Income support scheme for farmers providing Rs. 6000 per year in three installments',
        'description_translations': {
            'hi': 'किसानों के लिए आय सहायता योजना जो तीन किस्तों में प्रति वर्ष 6000 रुपये प्रदान करती है'
        },
        'benefits': [
            'Rs. 2000 per installment (3 times per year)',
            'Direct bank transfer',
            'No intermediaries'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'occupation': ['farmer'],
            'custom_criteria': {
                'land_ownership': 'yes',
                'cultivable_land': 'any'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'Bank account details',
            'Land ownership documents'
        ],
        'application_process': [
            'Visit PM-KISAN portal or nearest CSC',
            'Fill registration form with Aadhaar and bank details',
            'Upload land records',
            'Submit application',
            'Receive confirmation SMS'
        ],
        'application_url': 'https://pmkisan.gov.in',
        'department': 'Ministry of Agriculture and Farmers Welfare',
        'state': None,
        'last_updated': '2024-01-15T10:30:00',
        'source_url': 'https://pmkisan.gov.in'
    }


@pytest.fixture
def complex_scheme_item():
    """Create a scheme with complex eligibility criteria."""
    return {
        'scheme_id': 'COMPLEX-SCHEME-2024',
        'name': 'Complex Eligibility Scheme',
        'name_translations': {'hi': 'जटिल पात्रता योजना'},
        'category': 'social_welfare',
        'description': 'Scheme with complex eligibility criteria',
        'description_translations': {'hi': 'जटिल पात्रता मानदंड वाली योजना'},
        'benefits': ['Financial assistance', 'Healthcare support', 'Education support'],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'age_max': Decimal('60'),
            'income_max': Decimal('500000'),
            'gender': 'female',
            'occupation': ['farmer', 'laborer'],
            'education': ['primary', 'secondary'],
            'location': ['Rural'],
            'caste': ['SC', 'ST', 'OBC'],
            'custom_criteria': {
                'bpl_card': 'yes',
                'disability': 'any',
                'widow': 'yes'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'Income certificate',
            'Caste certificate',
            'BPL card',
            'Disability certificate (if applicable)',
            'Widow certificate (if applicable)'
        ],
        'application_process': [
            'Visit nearest Jan Seva Kendra',
            'Collect application form',
            'Fill form with all details',
            'Attach required documents',
            'Submit to concerned officer',
            'Collect acknowledgement receipt',
            'Track application status online'
        ],
        'application_url': 'https://example.gov.in/complex-scheme',
        'department': 'Social Welfare Department',
        'state': 'Uttar Pradesh',
        'last_updated': '2024-01-25T14:00:00',
        'source_url': 'https://example.gov.in/source'
    }


class TestSchemeDetailsIntegration:
    """Integration tests for scheme details with mocked DynamoDB."""
    
    @patch('src.core.base_repository.boto3')
    def test_get_scheme_details_success(self, mock_boto3, mock_dynamodb_table, sample_scheme_item):
        """Test successful retrieval of scheme details."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': sample_scheme_item}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'PM-KISAN-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify all required fields are present
        assert body['scheme_id'] == 'PM-KISAN-2024'
        assert body['name'] == 'Pradhan Mantri Kisan Samman Nidhi'
        assert body['category'] == 'agriculture'
        assert body['description'] == 'Income support scheme for farmers providing Rs. 6000 per year in three installments'
        
        # Verify translations
        assert 'name_translations' in body
        assert body['name_translations']['hi'] == 'प्रधानमंत्री किसान सम्मान निधि'
        assert 'description_translations' in body
        
        # Verify benefits
        assert len(body['benefits']) == 3
        assert 'Rs. 2000 per installment (3 times per year)' in body['benefits']
        
        # Verify eligibility criteria
        assert 'eligibility_criteria' in body
        assert body['eligibility_criteria']['age_min'] == 18
        assert body['eligibility_criteria']['occupation'] == ['farmer']
        
        # Verify required documents
        assert len(body['required_documents']) == 3
        assert 'Aadhaar card' in body['required_documents']
        
        # Verify application process
        assert len(body['application_process']) == 5
        assert 'Visit PM-KISAN portal or nearest CSC' in body['application_process']
        
        # Verify other fields
        assert body['application_url'] == 'https://pmkisan.gov.in'
        assert body['department'] == 'Ministry of Agriculture and Farmers Welfare'
        assert body['state'] is None
        assert body['source_url'] == 'https://pmkisan.gov.in'
        assert 'last_updated' in body
        
        # Verify DynamoDB was called correctly
        mock_dynamodb_table.get_item.assert_called_once_with(Key={'scheme_id': 'PM-KISAN-2024'})
    
    @patch('src.core.base_repository.boto3')
    def test_get_scheme_not_found(self, mock_boto3, mock_dynamodb_table):
        """Test retrieval of non-existent scheme."""
        # Setup mock - return empty response
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'NON-EXISTENT-SCHEME'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify 404 response
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()
    
    @patch('src.core.base_repository.boto3')
    def test_get_complex_scheme_with_all_criteria(self, mock_boto3, mock_dynamodb_table, complex_scheme_item):
        """Test retrieval of scheme with complex eligibility criteria."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': complex_scheme_item}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'COMPLEX-SCHEME-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify all eligibility criteria fields
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
        
        # Verify all required documents
        assert len(body['required_documents']) == 6
        assert 'Aadhaar card' in body['required_documents']
        assert 'Income certificate' in body['required_documents']
        assert 'Caste certificate' in body['required_documents']
        
        # Verify complete application process
        assert len(body['application_process']) == 7
        assert 'Visit nearest Jan Seva Kendra' in body['application_process']
        assert 'Track application status online' in body['application_process']
    
    @patch('src.core.base_repository.boto3')
    def test_response_format_compliance(self, mock_boto3, mock_dynamodb_table, sample_scheme_item):
        """Test that response format matches API specification (Requirement 2.2)."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': sample_scheme_item}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'PM-KISAN-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify response structure
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        
        # Verify all required fields per Requirement 2.2:
        # "scheme name, benefits, eligibility criteria, required documents, and application process"
        required_fields = [
            'scheme_id',
            'name',
            'name_translations',
            'category',
            'description',
            'description_translations',
            'benefits',
            'eligibility_criteria',
            'required_documents',
            'application_process',
            'application_url',
            'department',
            'state',
            'last_updated',
            'source_url'
        ]
        
        for field in required_fields:
            assert field in body, f"Missing required field: {field}"
    
    @patch('src.core.base_repository.boto3')
    def test_state_specific_scheme(self, mock_boto3, mock_dynamodb_table):
        """Test retrieval of state-specific scheme."""
        # Setup mock with state-specific scheme
        state_scheme = {
            'scheme_id': 'MH-FARMER-2024',
            'name': 'Maharashtra Farmer Support Scheme',
            'name_translations': {'mr': 'महाराष्ट्र शेतकरी सहाय्य योजना'},
            'category': 'agriculture',
            'description': 'State-level farmer support scheme',
            'description_translations': {'mr': 'राज्य स्तरीय शेतकरी सहाय्य योजना'},
            'benefits': ['Financial assistance', 'Crop insurance'],
            'eligibility_criteria': {
                'age_min': Decimal('18'),
                'occupation': ['farmer'],
                'location': ['Maharashtra']
            },
            'required_documents': ['Aadhaar', 'Land records'],
            'application_process': ['Visit district office', 'Submit application'],
            'application_url': 'https://maharashtra.gov.in/farmer-scheme',
            'department': 'Maharashtra Agriculture Department',
            'state': 'Maharashtra',
            'last_updated': '2024-01-20T12:00:00',
            'source_url': 'https://maharashtra.gov.in'
        }
        
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': state_scheme}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'MH-FARMER-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['state'] == 'Maharashtra'
        assert body['department'] == 'Maharashtra Agriculture Department'
        assert body['eligibility_criteria']['location'] == ['Maharashtra']
    
    @patch('src.core.base_repository.boto3')
    def test_cors_headers_present(self, mock_boto3, mock_dynamodb_table, sample_scheme_item):
        """Test that CORS headers are present in all responses."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': sample_scheme_item}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'PM-KISAN-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify CORS headers
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    @patch('src.core.base_repository.boto3')
    def test_invalid_scheme_id_parameter(self, mock_boto3, mock_dynamodb_table):
        """Test handling of invalid scheme_id parameter."""
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Test with empty scheme_id
        event = {
            'pathParameters': {
                'scheme_id': '   '
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        
        # Verify DynamoDB was not called
        mock_dynamodb_table.get_item.assert_not_called()
    
    @patch('src.core.base_repository.boto3')
    def test_complete_information_display(self, mock_boto3, mock_dynamodb_table, sample_scheme_item):
        """
        Test Property 5: Complete Information Display
        Validates: Requirements 2.2
        
        For any scheme displayed, the output should contain all required fields
        with no null or missing critical fields.
        """
        # Setup mock
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.get_item.return_value = {'Item': sample_scheme_item}
        
        # Execute
        event = {
            'pathParameters': {
                'scheme_id': 'PM-KISAN-2024'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Critical fields that must not be null or missing
        critical_fields = {
            'scheme_id': str,
            'name': str,
            'category': str,
            'description': str,
            'benefits': list,
            'eligibility_criteria': dict,
            'required_documents': list,
            'application_process': list,
            'department': str,
            'source_url': str
        }
        
        for field, expected_type in critical_fields.items():
            assert field in body, f"Critical field '{field}' is missing"
            assert body[field] is not None, f"Critical field '{field}' is null"
            assert isinstance(body[field], expected_type), f"Field '{field}' has wrong type"
            
            # For string fields, ensure they're not empty
            if expected_type == str:
                assert len(body[field].strip()) > 0, f"Critical field '{field}' is empty"
            
            # For list fields, ensure they're not empty
            if expected_type == list:
                assert len(body[field]) > 0, f"Critical field '{field}' is empty list"
            
            # For dict fields, ensure they're not empty
            if expected_type == dict:
                assert len(body[field]) > 0, f"Critical field '{field}' is empty dict"
