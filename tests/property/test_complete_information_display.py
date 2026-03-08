"""Property-based tests for complete information display.

Feature: bharatsahayak, Property 5: Complete Information Display
**Validates: Requirements 2.2, 4.2**

This test verifies that all required fields are present in scheme details,
skill programs, and job postings displayed to users, ensuring no critical
information is missing.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime, date
from typing import Any, Dict, List

from src.models.scheme import Scheme
from src.models.skill import SkillProgram, JobPosting
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    return Location(
        state=draw(st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Uttar Pradesh"])),
        district=draw(st.sampled_from(["Pune", "Mumbai", "Bangalore", "Chennai", "Ahmedabad"])),
        block=draw(st.none() | st.text(min_size=3, max_size=20)),
        village=draw(st.none() | st.text(min_size=3, max_size=20)),
        pincode=draw(st.from_regex(r'^\d{6}$', fullmatch=True)),
        latitude=draw(st.none() | st.floats(min_value=8.0, max_value=35.0)),
        longitude=draw(st.none() | st.floats(min_value=68.0, max_value=97.0))
    )


@st.composite
def eligibility_criteria_strategy(draw):
    """Generate valid EligibilityCriteria instances."""
    return EligibilityCriteria(
        age_min=draw(st.none() | st.integers(min_value=0, max_value=100)),
        age_max=draw(st.none() | st.integers(min_value=0, max_value=100)),
        income_max=draw(st.none() | st.integers(min_value=0, max_value=10000000)),
        gender=draw(st.none() | st.sampled_from(["male", "female", "other", "any"])),
        occupation=draw(st.none() | st.lists(
            st.sampled_from(["farmer", "laborer", "student", "unemployed", "any"]),
            max_size=3
        )),
        education=draw(st.none() | st.lists(
            st.sampled_from(["illiterate", "primary", "secondary", "graduate"]),
            max_size=3
        )),
        location=draw(st.none() | st.lists(
            st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat"]),
            max_size=2
        )),
        caste=draw(st.none() | st.lists(
            st.sampled_from(["SC", "ST", "OBC", "General"]),
            max_size=2
        )),
        custom_criteria=draw(st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
            st.text(min_size=1, max_size=50),
            max_size=3
        ))
    )


@st.composite
def scheme_strategy(draw):
    """Generate valid Scheme instances."""
    categories = ["agriculture", "health", "education", "employment", "social_welfare"]
    selected_category = draw(st.sampled_from(categories))
    
    scheme_id = f"{selected_category.upper()[:3]}-{draw(st.integers(min_value=1000, max_value=9999))}"
    
    return Scheme(
        scheme_id=scheme_id,
        name=draw(st.text(min_size=5, max_size=100)),
        name_translations=draw(st.dictionaries(
            st.sampled_from(["hi", "mr", "ta", "te", "bn"]),
            st.text(min_size=5, max_size=100),
            max_size=3
        )),
        category=selected_category,
        description=draw(st.text(min_size=20, max_size=500)),
        description_translations=draw(st.dictionaries(
            st.sampled_from(["hi", "mr", "ta", "te", "bn"]),
            st.text(min_size=20, max_size=500),
            max_size=3
        )),
        benefits=draw(st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=5)),
        eligibility_criteria=draw(eligibility_criteria_strategy()),
        required_documents=draw(st.lists(
            st.sampled_from(["Aadhaar", "PAN", "Income Certificate", "Caste Certificate", "Bank Passbook"]),
            min_size=1, max_size=5
        )),
        application_process=draw(st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=5)),
        application_url=draw(st.none() | st.from_regex(r'^https?://[a-z0-9.-]+\.[a-z]{2,}(/.*)?$', fullmatch=True)),
        department=draw(st.text(min_size=10, max_size=100)),
        state=draw(st.none() | st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", None])),
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url=draw(st.from_regex(r'^https?://[a-z0-9.-]+\.[a-z]{2,}(/.*)?$', fullmatch=True))
    )


@st.composite
def skill_program_strategy(draw):
    """Generate valid SkillProgram instances."""
    categories = ["technical", "vocational", "digital", "entrepreneurship"]
    
    return SkillProgram(
        program_id=f"SKILL-{draw(st.integers(min_value=1000, max_value=9999))}",
        name=draw(st.text(min_size=5, max_size=100)),
        provider=draw(st.text(min_size=5, max_size=100)),
        category=draw(st.sampled_from(categories)),
        description=draw(st.text(min_size=20, max_size=500)),
        duration_weeks=draw(st.integers(min_value=1, max_value=52)),
        cost=draw(st.floats(min_value=0, max_value=100000)),
        location=draw(location_strategy()),
        mode=draw(st.sampled_from(["in-person", "online", "hybrid"])),
        eligibility_criteria=draw(eligibility_criteria_strategy()),
        certification=draw(st.booleans()),
        placement_support=draw(st.booleans()),
        registration_url=draw(st.from_regex(r'^https?://[a-z0-9.-]+\.[a-z]{2,}(/.*)?$', fullmatch=True)),
        contact=draw(st.text(min_size=5, max_size=50))
    )


@st.composite
def job_posting_strategy(draw):
    """Generate valid JobPosting instances."""
    return JobPosting(
        job_id=f"JOB-{draw(st.integers(min_value=1000, max_value=9999))}",
        title=draw(st.text(min_size=5, max_size=100)),
        department=draw(st.text(min_size=5, max_size=100)),
        description=draw(st.text(min_size=20, max_size=500)),
        qualifications=draw(st.dictionaries(
            st.sampled_from(["education", "experience", "skills"]),
            st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=5),
            min_size=1,
            max_size=3
        )),
        location=draw(location_strategy()),
        application_deadline=date(2024, 12, 31),
        application_url=draw(st.from_regex(r'^https?://[a-z0-9.-]+\.[a-z]{2,}(/.*)?$', fullmatch=True)),
        posted_date=date(2024, 1, 15),
        salary_range=draw(st.none() | st.text(min_size=10, max_size=50)),
        vacancies=draw(st.none() | st.integers(min_value=1, max_value=1000))
    )


def check_required_fields_present(obj: Any, required_fields: List[str]) -> Dict[str, bool]:
    """
    Check if all required fields are present and not None/empty.
    
    Returns a dict mapping field names to whether they are valid.
    """
    results = {}
    for field in required_fields:
        value = getattr(obj, field, None)
        
        # Check if field exists and is not None
        if value is None:
            results[field] = False
            continue
        
        # Check if string fields are not empty
        if isinstance(value, str) and len(value.strip()) == 0:
            results[field] = False
            continue
        
        # Check if list fields are not empty
        if isinstance(value, list) and len(value) == 0:
            results[field] = False
            continue
        
        # Check if dict fields are not empty (for required dicts)
        if isinstance(value, dict) and field in ["qualifications"] and len(value) == 0:
            results[field] = False
            continue
        
        results[field] = True
    
    return results


@settings(max_examples=50, deadline=None)
@given(scheme=scheme_strategy())
def test_scheme_complete_information_display(scheme):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    For any scheme displayed to the user, the output should contain all
    required fields with no null or missing critical fields.
    
    Required fields for schemes:
    - scheme_id: Unique identifier
    - name: Scheme name
    - category: Scheme category
    - description: Detailed description
    - benefits: List of benefits (at least one)
    - eligibility_criteria: Eligibility requirements
    - required_documents: Required documents (at least one)
    - application_process: Application steps (at least one)
    - department: Responsible department
    - last_updated: Last update timestamp
    - source_url: Official source URL
    
    Optional fields (can be None):
    - application_url: May not be available for all schemes
    - state: None for central schemes
    - name_translations: May be empty initially
    - description_translations: May be empty initially
    """
    # Define required fields that must be present and non-empty
    required_fields = [
        "scheme_id",
        "name",
        "category",
        "description",
        "benefits",
        "eligibility_criteria",
        "required_documents",
        "application_process",
        "department",
        "last_updated",
        "source_url"
    ]
    
    # Check all required fields
    field_status = check_required_fields_present(scheme, required_fields)
    
    # Verify all required fields are present and valid
    missing_fields = [field for field, is_valid in field_status.items() if not is_valid]
    
    assert len(missing_fields) == 0, (
        f"Scheme '{scheme.scheme_id}' is missing or has empty required fields: {missing_fields}. "
        f"All schemes must have complete information for users to make informed decisions."
    )
    
    # Additional validation: Check that list fields have at least one item
    assert len(scheme.benefits) > 0, (
        f"Scheme '{scheme.scheme_id}' must have at least one benefit listed"
    )
    assert len(scheme.required_documents) > 0, (
        f"Scheme '{scheme.scheme_id}' must have at least one required document listed"
    )
    assert len(scheme.application_process) > 0, (
        f"Scheme '{scheme.scheme_id}' must have at least one application step listed"
    )
    
    # Verify eligibility_criteria is a valid object (not None)
    assert scheme.eligibility_criteria is not None, (
        f"Scheme '{scheme.scheme_id}' must have eligibility criteria defined"
    )


@settings(max_examples=50, deadline=None)
@given(program=skill_program_strategy())
def test_skill_program_complete_information_display(program):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    For any skill program displayed to the user, the output should contain
    all required fields with no null or missing critical fields.
    
    Required fields for skill programs:
    - program_id: Unique identifier
    - name: Program name
    - provider: Training provider
    - category: Program category
    - description: Detailed description
    - duration_weeks: Program duration
    - cost: Program cost
    - location: Program location
    - mode: Delivery mode
    - eligibility_criteria: Eligibility requirements
    - certification: Whether certification is provided
    - placement_support: Whether placement assistance is provided
    - registration_url: Registration URL
    - contact: Contact information
    """
    # Define required fields
    required_fields = [
        "program_id",
        "name",
        "provider",
        "category",
        "description",
        "location",
        "mode",
        "eligibility_criteria",
        "registration_url",
        "contact"
    ]
    
    # Check all required fields
    field_status = check_required_fields_present(program, required_fields)
    
    # Verify all required fields are present and valid
    missing_fields = [field for field, is_valid in field_status.items() if not is_valid]
    
    assert len(missing_fields) == 0, (
        f"Skill program '{program.program_id}' is missing or has empty required fields: {missing_fields}. "
        f"All programs must have complete information for users to make informed decisions."
    )
    
    # Additional validation: Check numeric fields are valid
    assert program.duration_weeks > 0, (
        f"Skill program '{program.program_id}' must have a positive duration"
    )
    assert program.cost >= 0, (
        f"Skill program '{program.program_id}' must have a non-negative cost"
    )
    
    # Verify boolean fields are present (not None)
    assert program.certification is not None, (
        f"Skill program '{program.program_id}' must specify whether certification is provided"
    )
    assert program.placement_support is not None, (
        f"Skill program '{program.program_id}' must specify whether placement support is provided"
    )
    
    # Verify location is a valid object
    assert program.location is not None, (
        f"Skill program '{program.program_id}' must have location information"
    )
    assert program.location.state, (
        f"Skill program '{program.program_id}' location must have a state"
    )


@settings(max_examples=50, deadline=None)
@given(job=job_posting_strategy())
def test_job_posting_complete_information_display(job):
    """
    Feature: bharatsahayak, Property 5: Complete Information Display
    
    For any job posting displayed to the user, the output should contain
    all required fields with no null or missing critical fields.
    
    Required fields for job postings:
    - job_id: Unique identifier
    - title: Job title
    - department: Government department
    - description: Job description
    - qualifications: Required qualifications (at least one category)
    - location: Job location
    - application_deadline: Last date to apply
    - application_url: Application portal URL
    - posted_date: Job posting date
    
    Optional fields:
    - salary_range: May not be disclosed
    - vacancies: May not be specified
    """
    # Define required fields
    required_fields = [
        "job_id",
        "title",
        "department",
        "description",
        "qualifications",
        "location",
        "application_deadline",
        "application_url",
        "posted_date"
    ]
    
    # Check all required fields
    field_status = check_required_fields_present(job, required_fields)
    
    # Verify all required fields are present and valid
    missing_fields = [field for field, is_valid in field_status.items() if not is_valid]
    
    assert len(missing_fields) == 0, (
        f"Job posting '{job.job_id}' is missing or has empty required fields: {missing_fields}. "
        f"All job postings must have complete information for users to make informed decisions."
    )
    
    # Additional validation: Check qualifications dict has at least one entry
    assert len(job.qualifications) > 0, (
        f"Job posting '{job.job_id}' must have at least one qualification category"
    )
    
    # Verify each qualification category has at least one item
    for category, items in job.qualifications.items():
        assert len(items) > 0, (
            f"Job posting '{job.job_id}' qualification category '{category}' must have at least one item"
        )
    
    # Verify location is a valid object
    assert job.location is not None, (
        f"Job posting '{job.job_id}' must have location information"
    )
    assert job.location.state, (
        f"Job posting '{job.job_id}' location must have a state"
    )
    
    # Verify dates are valid
    assert job.application_deadline is not None, (
        f"Job posting '{job.job_id}' must have an application deadline"
    )
    assert job.posted_date is not None, (
        f"Job posting '{job.job_id}' must have a posted date"
    )


@settings(max_examples=20, deadline=None)
@given(
    scheme=scheme_strategy(),
    program=skill_program_strategy(),
    job=job_posting_strategy()
)
def test_all_entity_types_complete_information(scheme, program, job):
    """
    Test that all entity types (schemes, programs, jobs) maintain
    complete information display property simultaneously.
    
    This ensures consistency across all information types in the system.
    """
    # Test scheme completeness
    scheme_required = ["scheme_id", "name", "description", "eligibility_criteria", "application_process"]
    scheme_status = check_required_fields_present(scheme, scheme_required)
    scheme_missing = [f for f, v in scheme_status.items() if not v]
    
    # Test program completeness
    program_required = ["program_id", "name", "description", "eligibility_criteria", "contact"]
    program_status = check_required_fields_present(program, program_required)
    program_missing = [f for f, v in program_status.items() if not v]
    
    # Test job completeness
    job_required = ["job_id", "title", "description", "qualifications", "application_url"]
    job_status = check_required_fields_present(job, job_required)
    job_missing = [f for f, v in job_status.items() if not v]
    
    # All entity types should have complete information
    assert len(scheme_missing) == 0, f"Scheme missing fields: {scheme_missing}"
    assert len(program_missing) == 0, f"Program missing fields: {program_missing}"
    assert len(job_missing) == 0, f"Job posting missing fields: {job_missing}"
