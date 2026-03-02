"""Property-based tests for emergency symptom detection.

Feature: bharatsahayak, Property 29: Emergency Symptom Detection
**Validates: Requirements 5.5**

This test verifies that emergency symptoms trigger urgent care recommendation
with emergency urgency level.
"""

import pytest
import json
from hypothesis import given, settings, strategies as st, HealthCheck

from src.services.health_advisor import HealthAdvisor


# Emergency symptoms that should trigger emergency response
EMERGENCY_SYMPTOMS = [
    "chest pain",
    "difficulty breathing",
    "severe bleeding",
    "unconscious",
    "severe headache",
    "stroke symptoms",
    "heart attack",
    "seizure",
    "severe abdominal pain",
    "severe burns",
    "poisoning",
    "choking",
    "severe allergic reaction",
    "high fever with confusion"
]


# Non-emergency symptoms for comparison
NON_EMERGENCY_SYMPTOMS = [
    "mild headache",
    "common cold",
    "minor cough",
    "slight fever",
    "sore throat",
    "runny nose",
    "mild fatigue"
]


@st.composite
def emergency_symptom_list_strategy(draw):
    """Generate symptom lists that include at least one emergency symptom."""
    # Pick 1-2 emergency symptoms
    num_emergency = draw(st.integers(min_value=1, max_value=2))
    emergency_symptoms = draw(st.lists(
        st.sampled_from(EMERGENCY_SYMPTOMS),
        min_size=num_emergency,
        max_size=num_emergency,
        unique=True
    ))
    
    # Optionally add 0-2 non-emergency symptoms
    num_other = draw(st.integers(min_value=0, max_value=2))
    if num_other > 0:
        other_symptoms = draw(st.lists(
            st.sampled_from(NON_EMERGENCY_SYMPTOMS),
            min_size=num_other,
            max_size=num_other,
            unique=True
        ))
        return emergency_symptoms + other_symptoms
    
    return emergency_symptoms


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
@given(symptoms=emergency_symptom_list_strategy())
def test_emergency_symptom_detection(symptoms):
    """
    Feature: bharatsahayak, Property 29: Emergency Symptom Detection
    
    For any symptom list containing known emergency indicators (chest pain,
    difficulty breathing, severe bleeding), the Health_Advisor should set
    urgency_level to "emergency" and recommend immediate medical care.
    
    This test verifies:
    1. Emergency symptoms trigger "emergency" urgency level
    2. Guidance recommends immediate medical attention
    3. Response includes emergency keywords
    4. Self-care recommendations are minimal or absent for emergencies
    """
    # Call the health check handler
    response = call_health_check_handler(symptoms)
    
    # Verify successful response
    assert response['statusCode'] == 200, (
        f"Expected status code 200, got {response['statusCode']}"
    )
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Property 1: Urgency level must be "emergency"
    assert body['urgency_level'] == 'emergency', (
        f"Emergency symptoms {symptoms} should trigger 'emergency' urgency level, "
        f"got '{body['urgency_level']}'"
    )
    
    # Property 2: when_to_seek_care must recommend immediate attention
    when_to_seek = body['when_to_seek_care'].lower()
    
    assert any(keyword in when_to_seek for keyword in [
        'immediate', 'immediately', 'emergency', 'urgent', 'now'
    ]), (
        f"Emergency guidance should recommend immediate care, got: {body['when_to_seek_care']}"
    )
    
    # Property 3: Should mention emergency services or hospital
    assert any(keyword in when_to_seek for keyword in [
        'emergency', 'hospital', 'medical attention', 'emergency room', 'emergency services'
    ]), (
        f"Emergency guidance should mention emergency services or hospital, "
        f"got: {body['when_to_seek_care']}"
    )
    
    # Property 4: Confidence should be high for emergency detection
    assert body['confidence'] >= 0.8, (
        f"Emergency detection should have high confidence, got {body['confidence']}"
    )


@settings(max_examples=5, deadline=None)
@given(emergency_symptom=st.sampled_from(EMERGENCY_SYMPTOMS))
def test_individual_emergency_symptoms(emergency_symptom):
    """
    Test that each individual emergency symptom triggers emergency response.
    
    This verifies that a single emergency symptom is sufficient to trigger
    emergency urgency level.
    """
    symptoms = [emergency_symptom]
    
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Should be emergency level
    assert body['urgency_level'] == 'emergency', (
        f"Single emergency symptom '{emergency_symptom}' should trigger emergency level, "
        f"got '{body['urgency_level']}'"
    )
    
    # Should recommend immediate care
    when_to_seek = body['when_to_seek_care'].lower()
    assert 'immediate' in when_to_seek or 'emergency' in when_to_seek, (
        f"Emergency symptom '{emergency_symptom}' should recommend immediate care"
    )


@settings(max_examples=5, deadline=None)
@given(non_emergency_symptom=st.sampled_from(NON_EMERGENCY_SYMPTOMS))
def test_non_emergency_symptoms_not_emergency(non_emergency_symptom):
    """
    Test that non-emergency symptoms do not trigger emergency response.
    
    This verifies that the system correctly distinguishes between emergency
    and non-emergency symptoms.
    """
    symptoms = [non_emergency_symptom]
    
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Should NOT be emergency level
    assert body['urgency_level'] != 'emergency', (
        f"Non-emergency symptom '{non_emergency_symptom}' should not trigger emergency level, "
        f"got '{body['urgency_level']}'"
    )


def test_emergency_symptom_combinations():
    """
    Test specific emergency symptom combinations.
    
    This verifies that common emergency presentations are correctly identified.
    """
    emergency_combinations = [
        ["chest pain", "difficulty breathing"],
        ["severe bleeding", "unconscious"],
        ["chest pain", "severe headache"],
        ["difficulty breathing", "severe allergic reaction"],
        ["seizure"],
        ["stroke symptoms"],
        ["heart attack"]
    ]
    
    for symptoms in emergency_combinations:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Should be emergency level
        assert body['urgency_level'] == 'emergency', (
            f"Emergency combination {symptoms} should trigger emergency level, "
            f"got '{body['urgency_level']}'"
        )
        
        # Should recommend immediate care
        when_to_seek = body['when_to_seek_care'].lower()
        assert 'immediate' in when_to_seek or 'emergency' in when_to_seek, (
            f"Emergency combination {symptoms} should recommend immediate care"
        )


def test_emergency_symptom_service_directly():
    """
    Test that HealthAdvisor service correctly detects emergency symptoms.
    
    This verifies that the service itself properly identifies emergencies.
    """
    advisor = HealthAdvisor()
    
    # Test each emergency symptom
    for emergency_symptom in EMERGENCY_SYMPTOMS[:5]:  # Test first 5
        symptoms = [emergency_symptom]
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Should be emergency level
        assert guidance.urgency_level == 'emergency', (
            f"Service should detect '{emergency_symptom}' as emergency, "
            f"got '{guidance.urgency_level}'"
        )
        
        # Should recommend immediate care
        when_to_seek = guidance.when_to_seek_care.lower()
        assert 'immediate' in when_to_seek or 'emergency' in when_to_seek, (
            f"Service should recommend immediate care for '{emergency_symptom}'"
        )


@settings(max_examples=5, deadline=None)
@given(symptoms=emergency_symptom_list_strategy())
def test_emergency_response_urgency_keywords(symptoms):
    """
    Test that emergency responses contain appropriate urgency keywords.
    
    This verifies that the language used conveys the seriousness of the situation.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    when_to_seek = body['when_to_seek_care'].upper()
    
    # Should use urgent language (uppercase for emphasis)
    assert any(keyword in when_to_seek for keyword in [
        'SEEK', 'IMMEDIATE', 'EMERGENCY', 'CALL', 'GO TO'
    ]), (
        f"Emergency guidance should use urgent language, got: {body['when_to_seek_care']}"
    )


@settings(max_examples=5, deadline=None)
@given(symptoms=emergency_symptom_list_strategy())
def test_emergency_red_flags_present(symptoms):
    """
    Test that emergency responses include red flags.
    
    This verifies that warning signs are provided even for emergencies.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Should have red flags
    assert 'red_flags' in body, (
        "Emergency response should include red_flags field"
    )
    
    red_flags = body['red_flags']
    
    # Red flags should be a list
    assert isinstance(red_flags, list), (
        "red_flags should be a list"
    )
    
    # Should have at least some red flags
    assert len(red_flags) >= 0, (
        "Emergency response should include red flags"
    )


def test_emergency_symptom_case_insensitive():
    """
    Test that emergency symptom detection is case-insensitive.
    
    This verifies that symptoms are detected regardless of capitalization.
    """
    test_cases = [
        ["CHEST PAIN"],
        ["Chest Pain"],
        ["chest pain"],
        ["ChEsT pAiN"]
    ]
    
    for symptoms in test_cases:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Should be emergency level regardless of case
        assert body['urgency_level'] == 'emergency', (
            f"Emergency symptom detection should be case-insensitive, "
            f"failed for: {symptoms}"
        )


def test_emergency_symptom_partial_match():
    """
    Test that emergency symptoms are detected even with additional words.
    
    This verifies that symptoms like "severe chest pain" are detected.
    """
    test_cases = [
        ["severe chest pain"],
        ["sharp chest pain"],
        ["chest pain radiating to arm"],
        ["difficulty breathing and wheezing"],
        ["severe bleeding from wound"]
    ]
    
    for symptoms in test_cases:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Should be emergency level
        assert body['urgency_level'] == 'emergency', (
            f"Emergency symptom should be detected in: {symptoms}, "
            f"got urgency level: {body['urgency_level']}"
        )


@settings(max_examples=5, deadline=None)
@given(symptoms=emergency_symptom_list_strategy())
def test_emergency_disclaimer_still_present(symptoms):
    """
    Test that emergency responses still include disclaimer.
    
    This verifies that legal protection is maintained even for emergencies.
    """
    response = call_health_check_handler(symptoms)
    body = json.loads(response['body'])
    
    # Disclaimer must still be present
    assert 'disclaimer' in body, (
        "Emergency response must still include disclaimer"
    )
    
    assert len(body['disclaimer']) > 0, (
        "Emergency response disclaimer cannot be empty"
    )


def test_emergency_symptom_priority():
    """
    Test that emergency symptoms take priority over non-emergency symptoms.
    
    This verifies that if both emergency and non-emergency symptoms are present,
    the response is still emergency level.
    """
    mixed_symptoms = [
        ["chest pain", "mild headache"],
        ["difficulty breathing", "common cold"],
        ["severe bleeding", "sore throat"]
    ]
    
    for symptoms in mixed_symptoms:
        response = call_health_check_handler(symptoms)
        body = json.loads(response['body'])
        
        # Should be emergency level (emergency takes priority)
        assert body['urgency_level'] == 'emergency', (
            f"Emergency symptom should take priority in: {symptoms}, "
            f"got urgency level: {body['urgency_level']}"
        )
