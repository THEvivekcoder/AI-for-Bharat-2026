"""Property-based tests for health disclaimer presence.

Feature: bharatsahayak, Property 14: Health Disclaimer Presence
**Validates: Requirements 5.3**

This test verifies that all health guidance responses include a disclaimer
stating that the advice is informational and not a substitute for professional
medical consultation.
"""

import pytest
import json
from hypothesis import given, settings, strategies as st, HealthCheck

from src.services.health_advisor import HealthAdvisor


# Custom strategies for generating valid test data
@st.composite
def symptom_list_strategy(draw):
    """Generate valid symptom lists."""
    common_symptoms = [
        "fever", "cough", "cold", "headache", "body ache", "sore throat",
        "stomach pain", "diarrhea", "nausea", "vomiting", "fatigue",
        "dizziness", "rash", "chest pain", "difficulty breathing",
        "severe bleeding", "unconscious", "seizure", "high fever"
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
def test_health_disclaimer_presence(symptoms):
    """
    Feature: bharatsahayak, Property 14: Health Disclaimer Presence
    
    For any health guidance output, the response should contain a disclaimer
    stating that the advice is informational and not a substitute for
    professional medical consultation.
    
    This test verifies:
    1. Disclaimer field is present
    2. Disclaimer is non-empty
    3. Disclaimer contains key phrases about medical advice
    4. Disclaimer is present for all urgency levels
    """
    # Call the health check handler
    response = call_health_check_handler(symptoms)
    
    # Verify successful response
    assert response['statusCode'] == 200, (
        f"Expected status code 200, got {response['statusCode']}"
    )
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Property 1: Disclaimer field must be present
    assert 'disclaimer' in body, (
        "Response must contain 'disclaimer' field"
    )
    
    disclaimer = body['disclaimer']
    
    # Property 2: Disclaimer must be a non-empty string
    assert isinstance(disclaimer, str), (
        "Disclaimer must be a string"
    )
    assert len(disclaimer) > 0, (
        "Disclaimer cannot be empty"
    )
    
    # Property 3: Disclaimer must contain key phrases
    # Convert to lowercase for case-insensitive matching
    disclaimer_lower = disclaimer.lower()
    
    # Must mention that it's informational/educational
    assert any(phrase in disclaimer_lower for phrase in [
        'informational', 'educational', 'information'
    ]), (
        "Disclaimer must state that advice is informational/educational"
    )
    
    # Must mention it's not a substitute for professional advice
    assert any(phrase in disclaimer_lower for phrase in [
        'not a substitute', 'not substitute', 'not replace'
    ]), (
        "Disclaimer must state that advice is not a substitute for professional care"
    )
    
    # Must mention professional medical advice/consultation
    assert any(phrase in disclaimer_lower for phrase in [
        'professional medical', 'medical advice', 'physician', 
        'health provider', 'medical consultation'
    ]), (
        "Disclaimer must mention professional medical advice or consultation"
    )
    
    # Property 4: Disclaimer should be substantial (not just a token phrase)
    assert len(disclaimer) >= 50, (
        f"Disclaimer should be substantial (at least 50 characters), got {len(disclaimer)}"
    )


@settings(max_examples=5, deadline=None)
@given(
    urgency_level=st.sampled_from(['routine', 'soon', 'urgent', 'emergency'])
)
def test_health_disclaimer_all_urgency_levels(urgency_level):
    """
    Test that disclaimer is present for all urgency levels.
    
    This verifies that even emergency guidance includes a disclaimer.
    """
    # Map urgency levels to appropriate symptoms
    symptom_map = {
        'routine': ['headache'],
        'soon': ['fever', 'cough'],
        'urgent': ['high fever', 'severe pain'],
        'emergency': ['chest pain', 'difficulty breathing']
    }
    
    symptoms = symptom_map[urgency_level]
    
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Verify disclaimer is present
    assert 'disclaimer' in body, (
        f"Disclaimer missing for urgency level: {urgency_level}"
    )
    
    disclaimer = body['disclaimer']
    
    # Verify disclaimer is non-empty
    assert len(disclaimer) > 0, (
        f"Disclaimer is empty for urgency level: {urgency_level}"
    )
    
    # Verify disclaimer contains key phrases
    disclaimer_lower = disclaimer.lower()
    assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, (
        f"Disclaimer missing key phrase for urgency level: {urgency_level}"
    )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_disclaimer_consistency(symptoms):
    """
    Test that disclaimer is consistent across calls.
    
    This verifies that the same disclaimer text is used consistently.
    """
    # Call twice with same symptoms
    response1 = call_health_check_handler(symptoms)
    response2 = call_health_check_handler(symptoms)
    
    body1 = json.loads(response1['body'])
    body2 = json.loads(response2['body'])
    
    # Disclaimers should be identical
    assert body1['disclaimer'] == body2['disclaimer'], (
        "Disclaimer should be consistent across calls"
    )


def test_health_disclaimer_service_directly():
    """
    Test that HealthAdvisor service always includes disclaimer.
    
    This verifies that the service itself enforces disclaimer presence.
    """
    advisor = HealthAdvisor()
    
    # Test with various symptom combinations
    test_cases = [
        ["fever"],
        ["cough", "cold"],
        ["chest pain"],
        ["headache", "nausea"],
        []  # Empty symptoms
    ]
    
    for symptoms in test_cases:
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Verify disclaimer is present
        assert hasattr(guidance, 'disclaimer'), (
            f"HealthGuidance missing disclaimer attribute for symptoms: {symptoms}"
        )
        
        assert guidance.disclaimer is not None, (
            f"Disclaimer is None for symptoms: {symptoms}"
        )
        
        assert len(guidance.disclaimer) > 0, (
            f"Disclaimer is empty for symptoms: {symptoms}"
        )
        
        # Verify disclaimer contains key phrases
        disclaimer_lower = guidance.disclaimer.lower()
        assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, (
            f"Disclaimer missing key phrase for symptoms: {symptoms}"
        )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_disclaimer_format(symptoms):
    """
    Test that disclaimer is properly formatted.
    
    This verifies that disclaimer is readable and well-structured.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    disclaimer = body['disclaimer']
    
    # Should be a complete sentence (ends with period)
    assert disclaimer.endswith('.') or disclaimer.endswith('!'), (
        "Disclaimer should end with proper punctuation"
    )
    
    # Should start with capital letter
    assert disclaimer[0].isupper(), (
        "Disclaimer should start with capital letter"
    )
    
    # Should not be excessively long (reasonable limit)
    assert len(disclaimer) <= 500, (
        f"Disclaimer is too long ({len(disclaimer)} characters), should be concise"
    )


def test_health_disclaimer_emergency_symptoms():
    """
    Test that emergency symptoms still include disclaimer.
    
    This is critical - even urgent care recommendations must include disclaimer.
    """
    emergency_symptoms = [
        ["chest pain"],
        ["difficulty breathing"],
        ["severe bleeding"],
        ["unconscious"]
    ]
    
    for symptoms in emergency_symptoms:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Verify disclaimer is present even for emergencies
        assert 'disclaimer' in body, (
            f"Disclaimer missing for emergency symptoms: {symptoms}"
        )
        
        disclaimer = body['disclaimer']
        
        assert len(disclaimer) > 0, (
            f"Disclaimer is empty for emergency symptoms: {symptoms}"
        )
        
        # Verify disclaimer contains key phrases
        disclaimer_lower = disclaimer.lower()
        assert 'not a substitute' in disclaimer_lower or 'not substitute' in disclaimer_lower, (
            f"Disclaimer missing key phrase for emergency symptoms: {symptoms}"
        )


@settings(max_examples=5, deadline=None)
@given(symptoms=symptom_list_strategy())
def test_health_disclaimer_content_quality(symptoms):
    """
    Test that disclaimer provides meaningful legal protection.
    
    This verifies that disclaimer is not just a token phrase but provides
    actual legal protection and guidance.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    disclaimer = body['disclaimer']
    
    # Should mention seeking professional advice
    disclaimer_lower = disclaimer.lower()
    assert any(phrase in disclaimer_lower for phrase in [
        'seek', 'consult', 'contact', 'advice'
    ]), (
        "Disclaimer should encourage seeking professional advice"
    )
    
    # Should mention medical professional or physician
    assert any(phrase in disclaimer_lower for phrase in [
        'physician', 'doctor', 'health provider', 'medical professional'
    ]), (
        "Disclaimer should mention medical professionals"
    )
    
    # Should be clear about limitations
    assert any(phrase in disclaimer_lower for phrase in [
        'not a substitute', 'not substitute', 'not replace', 
        'informational', 'educational'
    ]), (
        "Disclaimer should clearly state limitations"
    )


def test_health_disclaimer_model_validation():
    """
    Test that HealthGuidance model enforces disclaimer requirement.
    
    This verifies that the data model itself requires a disclaimer.
    """
    from src.models.health import HealthGuidance
    
    # Try to create guidance without disclaimer (should fail)
    with pytest.raises(Exception):  # Pydantic validation error
        HealthGuidance(
            urgency_level="routine",
            possible_conditions=[],
            self_care_recommendations=[],
            when_to_seek_care="Consult a doctor",
            red_flags=[],
            # Missing disclaimer - should fail
        )
    
    # Create guidance with disclaimer (should succeed)
    guidance = HealthGuidance(
        urgency_level="routine",
        possible_conditions=[],
        self_care_recommendations=[],
        when_to_seek_care="Consult a doctor",
        red_flags=[],
        disclaimer="This is a test disclaimer.",
        confidence=0.5
    )
    
    assert guidance.disclaimer == "This is a test disclaimer."
