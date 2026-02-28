"""
Unit Test: Emergency Symptom Detection
Feature: bharatsahayak, Property 29: Emergency Symptom Detection

For any symptom list containing known emergency indicators (chest pain, 
difficulty breathing, severe bleeding), the Health_Advisor should set 
urgency_level to "emergency" and recommend immediate medical care.

Validates: Requirements 5.5
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.health_advisor import HealthAdvisor
from app.schemas.health import BasicHealthInfo


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Float, Integer, JSON, DECIMAL
    from sqlalchemy import MetaData
    import uuid as uuid_module
    
    class UUID(TypeDecorator):
        """Platform-independent UUID type."""
        impl = CHAR
        cache_ok = True
        
        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                return dialect.type_descriptor(PG_UUID())
            else:
                return dialect.type_descriptor(CHAR(36))
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif not isinstance(value, uuid_module.UUID):
                return str(uuid_module.UUID(value)) if value else None
            else:
                return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid_module.UUID(value) if value else None
    
    # Create engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create tables manually for SQLite compatibility
    metadata = MetaData()
    
    # Health facilities table
    health_facilities_table = Table(
        'health_facilities', metadata,
        Column('facility_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('facility_type', String(50)),
        Column('state', String(50)),
        Column('district', String(50)),
        Column('address', Text),
        Column('latitude', DECIMAL(10, 8)),
        Column('longitude', DECIMAL(11, 8)),
        Column('contact', String(100)),
        Column('services', JSON),
        Column('created_at', DateTime)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestEmergencySymptomDetection:
    """Test suite for emergency symptom detection (Property 29)"""
    
    def test_chest_pain_triggers_emergency(self, test_db_session):
        """Test that chest pain triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Chest pain should trigger emergency urgency level"
        
        # Verify immediate care recommendation
        when_to_seek_care_lower = guidance.when_to_seek_care.lower()
        assert 'immediate' in when_to_seek_care_lower or 'now' in when_to_seek_care_lower or 'emergency' in when_to_seek_care_lower, \
            "Emergency guidance should recommend immediate medical care"
    
    def test_difficulty_breathing_triggers_emergency(self, test_db_session):
        """Test that difficulty breathing triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['difficulty breathing']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Difficulty breathing should trigger emergency urgency level"
        
        # Verify immediate care recommendation
        assert 'immediate' in guidance.when_to_seek_care.lower() or 'emergency' in guidance.when_to_seek_care.lower(), \
            "Should recommend immediate emergency care"
    
    def test_severe_bleeding_triggers_emergency(self, test_db_session):
        """Test that severe bleeding triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe bleeding']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe bleeding should trigger emergency urgency level"
        
        # Verify immediate care recommendation
        assert 'immediate' in guidance.when_to_seek_care.lower() or 'emergency' in guidance.when_to_seek_care.lower(), \
            "Should recommend immediate emergency care"
    
    def test_unconscious_triggers_emergency(self, test_db_session):
        """Test that unconsciousness triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['unconscious']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Unconsciousness should trigger emergency urgency level"
    
    def test_seizure_triggers_emergency(self, test_db_session):
        """Test that seizure triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['seizure']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Seizure should trigger emergency urgency level"
    
    def test_severe_head_injury_triggers_emergency(self, test_db_session):
        """Test that severe head injury triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe head injury']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe head injury should trigger emergency urgency level"
    
    def test_stroke_symptoms_triggers_emergency(self, test_db_session):
        """Test that stroke symptoms trigger emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['stroke symptoms']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Stroke symptoms should trigger emergency urgency level"
    
    def test_heart_attack_triggers_emergency(self, test_db_session):
        """Test that heart attack triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['heart attack']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Heart attack should trigger emergency urgency level"
    
    def test_severe_abdominal_pain_triggers_emergency(self, test_db_session):
        """Test that severe abdominal pain triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe abdominal pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe abdominal pain should trigger emergency urgency level"
    
    def test_poisoning_triggers_emergency(self, test_db_session):
        """Test that poisoning triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['poisoning']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Poisoning should trigger emergency urgency level"
    
    def test_severe_burns_triggers_emergency(self, test_db_session):
        """Test that severe burns trigger emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe burns']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe burns should trigger emergency urgency level"
    
    def test_choking_triggers_emergency(self, test_db_session):
        """Test that choking triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['choking']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Choking should trigger emergency urgency level"
    
    def test_severe_allergic_reaction_triggers_emergency(self, test_db_session):
        """Test that severe allergic reaction triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe allergic reaction']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe allergic reaction should trigger emergency urgency level"
    
    def test_loss_of_consciousness_triggers_emergency(self, test_db_session):
        """Test that loss of consciousness triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['loss of consciousness']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Loss of consciousness should trigger emergency urgency level"
    
    def test_paralysis_triggers_emergency(self, test_db_session):
        """Test that paralysis triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['paralysis']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Paralysis should trigger emergency urgency level"
    
    def test_severe_trauma_triggers_emergency(self, test_db_session):
        """Test that severe trauma triggers emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['severe trauma']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Severe trauma should trigger emergency urgency level"
    
    def test_multiple_emergency_symptoms(self, test_db_session):
        """Test that multiple emergency symptoms trigger emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain', 'difficulty breathing', 'severe bleeding']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Multiple emergency symptoms should trigger emergency urgency level"
    
    def test_emergency_symptom_with_routine_symptoms(self, test_db_session):
        """Test that emergency symptom mixed with routine symptoms still triggers emergency"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['fever', 'chest pain', 'headache']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Emergency symptom mixed with routine symptoms should still trigger emergency urgency level"
    
    def test_emergency_symptom_case_insensitive(self, test_db_session):
        """Test that emergency symptom detection is case-insensitive"""
        advisor = HealthAdvisor(test_db_session)
        
        # Test uppercase
        symptoms_upper = ['CHEST PAIN']
        guidance_upper = advisor.analyze_symptoms(symptoms_upper)
        
        assert guidance_upper.urgency_level == 'emergency', \
            "Emergency symptom detection should be case-insensitive (uppercase)"
        
        # Test mixed case
        symptoms_mixed = ['Chest Pain']
        guidance_mixed = advisor.analyze_symptoms(symptoms_mixed)
        
        assert guidance_mixed.urgency_level == 'emergency', \
            "Emergency symptom detection should be case-insensitive (mixed case)"
    
    def test_emergency_symptom_with_extra_whitespace(self, test_db_session):
        """Test that emergency symptom detection handles extra whitespace"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['  chest pain  ']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Emergency symptom detection should handle extra whitespace"
    
    def test_emergency_symptom_substring_match(self, test_db_session):
        """Test that emergency symptoms are detected as substrings"""
        advisor = HealthAdvisor(test_db_session)
        
        # "chest pain" should be detected in "severe chest pain"
        symptoms = ['severe chest pain radiating to arm']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Emergency symptom should be detected as substring in longer description"
    
    def test_emergency_self_care_recommendations(self, test_db_session):
        """Test that emergency symptoms provide appropriate self-care recommendations"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Emergency self-care should recommend seeking immediate care
        assert len(guidance.self_care_recommendations) > 0, \
            "Emergency guidance should have self-care recommendations"
        
        recommendations_text = ' '.join(guidance.self_care_recommendations).lower()
        assert 'emergency' in recommendations_text or 'immediate' in recommendations_text or 'hospital' in recommendations_text, \
            "Emergency self-care recommendations should mention emergency/immediate care"
    
    def test_emergency_disclaimer_present(self, test_db_session):
        """Test that emergency symptoms still include disclaimer"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.disclaimer is not None, \
            "Emergency guidance should include disclaimer"
        assert len(guidance.disclaimer) > 0, \
            "Emergency guidance disclaimer should not be empty"
        assert 'not a substitute' in guidance.disclaimer.lower(), \
            "Emergency guidance should still include standard disclaimer"
    
    def test_emergency_with_user_info(self, test_db_session):
        """Test that emergency detection works with user info provided"""
        advisor = HealthAdvisor(test_db_session)
        
        user_info = BasicHealthInfo(
            age=65,
            gender='male',
            existing_conditions=['diabetes', 'hypertension'],
            medications=['metformin', 'aspirin']
        )
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms, user_info)
        
        assert guidance.urgency_level == 'emergency', \
            "Emergency detection should work with user info provided"
    
    def test_non_emergency_symptoms_not_flagged(self, test_db_session):
        """Test that non-emergency symptoms don't trigger emergency urgency level"""
        advisor = HealthAdvisor(test_db_session)
        
        # Common cold symptoms
        symptoms = ['fever', 'cough', 'runny nose']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level != 'emergency', \
            "Non-emergency symptoms should not trigger emergency urgency level"
        assert guidance.urgency_level in ['routine', 'soon', 'urgent'], \
            f"Non-emergency symptoms should have routine/soon/urgent urgency, got {guidance.urgency_level}"
    
    def test_partial_emergency_keyword_not_triggered(self, test_db_session):
        """Test that partial matches of emergency keywords don't trigger false positives"""
        advisor = HealthAdvisor(test_db_session)
        
        # "pain" alone should not trigger "chest pain" emergency
        symptoms = ['pain in leg']
        guidance = advisor.analyze_symptoms(symptoms)
        
        # This should not be emergency (just "pain" without "chest")
        # Note: Based on implementation, this might be urgent due to "pain" keyword
        # but should not be emergency
        assert guidance.urgency_level != 'emergency', \
            "Partial keyword match should not trigger emergency"
    
    def test_emergency_confidence_score(self, test_db_session):
        """Test that emergency symptoms have a valid confidence score"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert 0.0 <= guidance.confidence <= 1.0, \
            f"Confidence score should be between 0 and 1, got {guidance.confidence}"
    
    def test_emergency_red_flags_present(self, test_db_session):
        """Test that emergency symptoms include red flags"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['chest pain']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert len(guidance.red_flags) > 0, \
            "Emergency guidance should include red flags"
        
        # Should mention experiencing emergency symptoms
        red_flags_text = ' '.join(guidance.red_flags).lower()
        assert 'emergency' in red_flags_text, \
            "Red flags should mention emergency symptoms"
    
    def test_all_emergency_symptoms_from_constant(self, test_db_session):
        """Test all emergency symptoms defined in EMERGENCY_SYMPTOMS constant"""
        advisor = HealthAdvisor(test_db_session)
        
        # Test each emergency symptom from the constant
        for emergency_symptom in advisor.EMERGENCY_SYMPTOMS:
            symptoms = [emergency_symptom]
            guidance = advisor.analyze_symptoms(symptoms)
            
            assert guidance.urgency_level == 'emergency', \
                f"Emergency symptom '{emergency_symptom}' should trigger emergency urgency level"
            
            # Verify immediate care recommendation
            when_to_seek_care_lower = guidance.when_to_seek_care.lower()
            assert 'immediate' in when_to_seek_care_lower or 'emergency' in when_to_seek_care_lower or 'now' in when_to_seek_care_lower, \
                f"Emergency symptom '{emergency_symptom}' should recommend immediate care"


class TestEmergencySymptomEdgeCases:
    """Test edge cases for emergency symptom detection"""
    
    def test_empty_symptom_list(self, test_db_session):
        """Test handling of empty symptom list"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = []
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Should not be emergency with no symptoms
        assert guidance.urgency_level != 'emergency', \
            "Empty symptom list should not trigger emergency"
    
    def test_whitespace_only_symptom(self, test_db_session):
        """Test handling of whitespace-only symptom"""
        advisor = HealthAdvisor(test_db_session)
        
        symptoms = ['   ', '  ']
        guidance = advisor.analyze_symptoms(symptoms)
        
        # Should not be emergency with whitespace-only symptoms
        assert guidance.urgency_level != 'emergency', \
            "Whitespace-only symptoms should not trigger emergency"
    
    def test_emergency_symptom_in_longer_description(self, test_db_session):
        """Test emergency symptom detection in detailed descriptions"""
        advisor = HealthAdvisor(test_db_session)
        
        # Realistic user description
        symptoms = ['I have been experiencing chest pain for the last hour']
        guidance = advisor.analyze_symptoms(symptoms)
        
        assert guidance.urgency_level == 'emergency', \
            "Emergency symptom in longer description should be detected"
    
    def test_similar_but_not_emergency_symptom(self, test_db_session):
        """Test that similar but non-emergency symptoms are not flagged"""
        advisor = HealthAdvisor(test_db_session)
        
        # "chest congestion" is not the same as "chest pain"
        symptoms = ['chest congestion']
        guidance = advisor.analyze_symptoms(symptoms)
        
        # This should not be emergency (congestion != pain)
        # Note: Implementation uses substring matching, so this test verifies
        # that "chest pain" is not detected in "chest congestion"
        assert guidance.urgency_level != 'emergency', \
            "Similar but non-emergency symptoms should not trigger emergency"
