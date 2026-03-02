"""Property-based tests for health guidance generation.

Feature: bharatsahayak, Property 12: Health Guidance Generation
**Validates: Requirements 5.1**

This test verifies that health guidance contains all required fields
(urgency_level, possible_conditions, self_care_recommendations,
when_to_seek_care, disclaimer) for any list of symptoms.
"""

import pytest
import json
from hypothesis import given, settings, strategies as st, HealthCheck
from unittest.mock import patch

from src.services.health_advisor import HealthAdvisor


# Custom strategies for generating valid test data
@st.composite
def symptom_list_strategy(draw):
    """Generate valid symptom lists."""
    common_symptoms = [
        "fever", "cough", "cold", "headache", "body ache", "sore throat",
        "stomach pain", "diarrhea", "nausea", "vomiting", "fatigue",
        "dizziness", "rash", "chest pain", "difficulty breathing"
    ]
    
    # Generate 1-5 symptoms
    num_symptoms = draw(st.integers(min_value=1, max_value=5))
    symptoms = draw(st.lists(
        st.sampled_from(common_symptoms),
        min_size=num_symptoms,
        max_size=num_symptoms,
        unique=True
    ))
    
    return symptoms


def call_health_check_handler(symptoms: list) -> dict:
    """
    Call the health check Lambda handler.
    
    Args:
        symptoms: List of symptom strings
        
    Returns:
        Response dictionary from the handler
    """
    from src.api.health_check import lambda_handler
    
    # Create Lambda event
    event = {
        'body': json.dumps({
            'symptoms': symptoms
        }),
        'httpMethod': 'POST',
        'path': '/health/check'
    }
    
    # Call handler
    response = lambda_handler(event, None)
    
    return response


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(symptoms=symptom_list_strategy())
def test_health_guidance_generation(symptoms):
    """
    Feature: bharatsahayak, Property 12: Health Guidance Generation
    
    For any list of symptoms, the Health_Advisor should generate guidance
    containing urgency_level, possible_conditions, self_care_recommendations,
    when_to_seek_care, and disclaimer fields.
    
    This test verifies:
    1. All required fields are present
    2. Fields have appropriate types
    3. Urgency level is valid
    4. Disclaimer is always included
    """
    # Call the health check handler
    response = call_health_check_handler(symptoms)
    
    # Verify successful response
    assert response['statusCode'] == 200, (
        f"Expected status code 200, got {response['statusCode']}"
    )
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Property 1: All required fields must be present
    required_fields = [
        'urgency_level',
        'possible_conditions',
        'self_care_recommendations',
        'when_to_seek_care',
        'disclaimer',
        'red_flags',
        'confidence'
    ]
    
    for field in required_fields:
        assert field in body, f"Missing required field: {field}"
    
    # Property 2: urgency_level must be valid
    valid_urgency_levels = ['routine', 'soon', 'urgent', 'emergency']
    assert body['urgency_level'] in valid_urgency_levels, (
        f"Invalid urgency_level: {body['urgency_level']}, "
        f"must be one of {valid_urgency_levels}"
    )
    
    # Property 3: possible_conditions must be a list
    assert isinstance(body['possible_conditions'], list), (
        "possible_conditions must be a list"
    )
    
    # Property 4: self_care_recommendations must be a list
    assert isinstance(body['self_care_recommendations'], list), (
        "self_care_recommendations must be a list"
    )
    
    # Property 5: when_to_seek_care must be a non-empty string
    assert isinstance(body['when_to_seek_care'], str), (
        "when_to_seek_care must be a string"
    )
    assert len(body['when_to_seek_care']) > 0, (
        "when_to_seek_care cannot be empty"
    )
    
    # Property 6: disclaimer must be a non-empty string
    assert isinstance(body['disclaimer'], str), (
        "disclaimer must be a string"
    )
    assert len(body['disclaimer']) > 0, (
        "disclaimer cannot be empty"
    )
    
    # Property 7: red_flags must be a list
    assert isinstance(body['red_flags'], list), (
        "red_flags must be a list"
    )
    
    # Property 8: confidence must be a number between 0 and 1
    assert isinstance(body['confidence'], (int, float)), (
        "confidence must be a number"
    )
    assert 0 <= body['confidence'] <= 1, (
        f"confidence must be between 0 and 1, got {body['confidence']}"
    )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_guidance_completeness(symptoms):
    """
    Test that guidance provides meaningful content.
    
    This verifies that the guidance is not just empty placeholders.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Urgency level should be set
    assert body['urgency_level'] in ['routine', 'soon', 'urgent', 'emergency']
    
    # Should have when_to_seek_care guidance
    assert len(body['when_to_seek_care']) > 20, (
        "when_to_seek_care should provide meaningful guidance"
    )
    
    # Disclaimer should be substantial
    assert len(body['disclaimer']) > 50, (
        "disclaimer should be a complete medical disclaimer"
    )


@settings(max_examples=3, deadline=None)
@given(
    symptom1=st.sampled_from(["fever", "cough", "headache"]),
    symptom2=st.sampled_from(["body ache", "sore throat", "fatigue"])
)
def test_health_guidance_consistency(symptom1, symptom2):
    """
    Test that similar symptom combinations produce consistent guidance.
    
    This verifies that the same symptoms always produce the same urgency level.
    """
    symptoms = [symptom1, symptom2]
    
    # Call twice with same symptoms
    response1 = call_health_check_handler(symptoms)
    response2 = call_health_check_handler(symptoms)
    
    body1 = json.loads(response1['body'])
    body2 = json.loads(response2['body'])
    
    # Should produce same urgency level
    assert body1['urgency_level'] == body2['urgency_level'], (
        "Same symptoms should produce consistent urgency level"
    )
    
    # Should produce same possible conditions
    assert body1['possible_conditions'] == body2['possible_conditions'], (
        "Same symptoms should produce consistent possible conditions"
    )


def test_health_guidance_emergency_symptoms():
    """
    Test that emergency symptoms trigger emergency urgency level.
    
    This verifies that critical symptoms are properly identified.
    """
    emergency_symptoms = [
        ["chest pain"],
        ["difficulty breathing"],
        ["severe bleeding"],
        ["chest pain", "difficulty breathing"]
    ]
    
    for symptoms in emergency_symptoms:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Should be emergency level
        assert body['urgency_level'] == 'emergency', (
            f"Symptoms {symptoms} should trigger emergency urgency level, "
            f"got {body['urgency_level']}"
        )
        
        # Should recommend immediate care
        assert 'immediate' in body['when_to_seek_care'].lower() or \
               'emergency' in body['when_to_seek_care'].lower(), (
            f"Emergency symptoms should recommend immediate care"
        )


def test_health_guidance_invalid_input():
    """
    Test that invalid input returns appropriate error response.
    
    This verifies error handling for malformed requests.
    """
    from src.api.health_check import lambda_handler
    
    # Test with empty symptoms list
    event = {
        'body': json.dumps({
            'symptoms': []
        }),
        'httpMethod': 'POST',
        'path': '/health/check'
    }
    
    response = lambda_handler(event, None)
    
    # Should return 400 error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for empty symptoms, got {response['statusCode']}"
    )
    
    # Test with missing symptoms field
    event = {
        'body': json.dumps({}),
        'httpMethod': 'POST',
        'path': '/health/check'
    }
    
    response = lambda_handler(event, None)
    
    # Should return 400 error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for missing symptoms, got {response['statusCode']}"
    )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_guidance_self_care_recommendations(symptoms):
    """
    Test that self-care recommendations are provided.
    
    This verifies that guidance includes actionable self-care advice.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Should have self-care recommendations (unless emergency)
    if body['urgency_level'] != 'emergency':
        assert len(body['self_care_recommendations']) > 0, (
            "Non-emergency guidance should include self-care recommendations"
        )
        
        # Each recommendation should be a non-empty string
        for i, rec in enumerate(body['self_care_recommendations']):
            assert isinstance(rec, str), (
                f"Recommendation {i} should be a string"
            )
            assert len(rec) > 0, (
                f"Recommendation {i} should not be empty"
            )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_guidance_red_flags(symptoms):
    """
    Test that red flags (warning signs) are provided.
    
    This verifies that guidance includes warning signs to watch for.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Should have red flags
    assert isinstance(body['red_flags'], list), (
        "red_flags should be a list"
    )
    
    # Each red flag should be a non-empty string
    for i, flag in enumerate(body['red_flags']):
        assert isinstance(flag, str), (
            f"Red flag {i} should be a string"
        )
        assert len(flag) > 0, (
            f"Red flag {i} should not be empty"
        )


def test_health_guidance_service_directly():
    """
    Test the HealthAdvisor service directly.
    
    This verifies that the service works independently of the Lambda handler.
    """
    advisor = HealthAdvisor()
    
    # Test with common symptoms
    symptoms = ["fever", "cough", "cold"]
    guidance = advisor.analyze_symptoms(symptoms)
    
    # Verify all required fields
    assert guidance.urgency_level in ['routine', 'soon', 'urgent', 'emergency']
    assert isinstance(guidance.possible_conditions, list)
    assert isinstance(guidance.self_care_recommendations, list)
    assert isinstance(guidance.when_to_seek_care, str)
    assert len(guidance.when_to_seek_care) > 0
    assert isinstance(guidance.disclaimer, str)
    assert len(guidance.disclaimer) > 0
    assert isinstance(guidance.red_flags, list)
    assert 0 <= guidance.confidence <= 1
