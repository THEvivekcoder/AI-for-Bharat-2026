"""
Property-Based Test: Scheme Search Relevance
Feature: bharatsahayak, Property 4: Scheme Search Relevance

For any user query about government schemes, the System should retrieve schemes 
from the Scheme_Database where the scheme description, category, or benefits 
semantically match the query context.

Validates: Requirements 2.1, 5.4
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.scheme import Scheme, SchemeTranslation
from app.services.scheme_repository import SchemeRepository
from app.schemas.scheme import SchemeFilters
import uuid


# Strategy for generating eligibility criteria
@composite
def eligibility_criteria_strategy(draw):
    """Generate valid eligibility criteria"""
    criteria = {}
    
    # Randomly include various criteria
    if draw(st.booleans()):
        criteria['age_min'] = draw(st.integers(min_value=0, max_value=18))
    if draw(st.booleans()):
        criteria['age_max'] = draw(st.integers(min_value=18, max_value=100))
    if draw(st.booleans()):
        criteria['income_max'] = draw(st.integers(min_value=50000, max_value=500000))
    if draw(st.booleans()):
        criteria['gender'] = draw(st.sampled_from(['Male', 'Female', 'Any']))
    if draw(st.booleans()):
        criteria['occupation'] = draw(st.lists(
            st.sampled_from(['Farmer', 'Student', 'Worker', 'Self-Employed', 'Unemployed']),
            min_size=1, max_size=3
        ))
    if draw(st.booleans()):
        criteria['location'] = draw(st.lists(
            st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar']),
            min_size=1, max_size=3
        ))
    
    return criteria


# Strategy for generating schemes
@composite
def scheme_strategy(draw):
    """Generate a valid government scheme"""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    category = draw(st.sampled_from(categories))
    
    # Generate category-specific content
    scheme_templates = {
        'agriculture': {
            'names': [
                'PM-KISAN Scheme',
                'Crop Insurance Scheme',
                'Soil Health Card Scheme',
                'Kisan Credit Card',
                'Pradhan Mantri Fasal Bima Yojana'
            ],
            'descriptions': [
                'Provides financial assistance to farmers for agricultural activities',
                'Offers insurance coverage for crop losses due to natural calamities',
                'Helps farmers assess soil health and improve productivity',
                'Provides credit facilities to farmers for agricultural needs',
                'Protects farmers against crop failure and ensures income stability'
            ],
            'benefits': [
                ['Direct income support', 'Rs 6000 per year', 'Three installments'],
                ['Crop insurance', 'Premium subsidy', 'Quick claim settlement'],
                ['Free soil testing', 'Fertilizer recommendations', 'Improved yield'],
                ['Easy credit access', 'Low interest rates', 'Flexible repayment'],
                ['Risk coverage', 'Financial security', 'Timely compensation']
            ]
        },
        'health': {
            'names': [
                'Ayushman Bharat Scheme',
                'Pradhan Mantri Jan Arogya Yojana',
                'National Health Mission',
                'Free Medicine Scheme',
                'Maternal Health Program'
            ],
            'descriptions': [
                'Provides health insurance coverage for poor and vulnerable families',
                'Offers cashless treatment at empaneled hospitals',
                'Strengthens healthcare infrastructure in rural areas',
                'Provides free essential medicines at government facilities',
                'Ensures safe motherhood and reduces maternal mortality'
            ],
            'benefits': [
                ['Health insurance', 'Rs 5 lakh coverage', 'Cashless treatment'],
                ['Free hospitalization', 'Pre and post hospitalization', 'No cap on family size'],
                ['Better healthcare access', 'Quality services', 'Affordable treatment'],
                ['Free medicines', 'Essential drugs', 'Reduced healthcare costs'],
                ['Free delivery', 'Antenatal care', 'Postnatal support']
            ]
        },
        'education': {
            'names': [
                'Mid-Day Meal Scheme',
                'Scholarship for Students',
                'Sarva Shiksha Abhiyan',
                'Digital India Education',
                'Skill Development Program'
            ],
            'descriptions': [
                'Provides nutritious meals to school children',
                'Offers financial assistance for education',
                'Ensures universal access to quality education',
                'Promotes digital literacy and online learning',
                'Provides vocational training and skill enhancement'
            ],
            'benefits': [
                ['Free meals', 'Improved nutrition', 'Better attendance'],
                ['Financial support', 'Merit-based awards', 'Reduced dropout'],
                ['Free education', 'Quality teachers', 'Better infrastructure'],
                ['Digital resources', 'Online courses', 'Technology access'],
                ['Job-oriented training', 'Certification', 'Employment support']
            ]
        },
        'employment': {
            'names': [
                'MGNREGA Employment Scheme',
                'Pradhan Mantri Rozgar Yojana',
                'Self Employment Scheme',
                'Youth Employment Program',
                'Rural Employment Guarantee'
            ],
            'descriptions': [
                'Guarantees 100 days of wage employment in rural areas',
                'Provides financial assistance for self-employment',
                'Supports entrepreneurship and business development',
                'Creates employment opportunities for youth',
                'Ensures livelihood security in rural areas'
            ],
            'benefits': [
                ['Guaranteed employment', 'Minimum wages', 'Asset creation'],
                ['Loan subsidy', 'Business support', 'Training assistance'],
                ['Financial aid', 'Mentorship', 'Market linkages'],
                ['Job placement', 'Skill training', 'Career guidance'],
                ['Income security', 'Social protection', 'Rural development']
            ]
        },
        'social_welfare': {
            'names': [
                'Pension Scheme for Elderly',
                'Widow Pension Scheme',
                'Disability Pension Program',
                'Housing for All Scheme',
                'LPG Subsidy Scheme'
            ],
            'descriptions': [
                'Provides monthly pension to senior citizens',
                'Offers financial support to widows',
                'Ensures income security for persons with disabilities',
                'Provides affordable housing to economically weaker sections',
                'Subsidizes cooking gas for poor households'
            ],
            'benefits': [
                ['Monthly pension', 'Financial security', 'Social protection'],
                ['Regular income', 'Economic support', 'Dignity'],
                ['Disability pension', 'Healthcare support', 'Rehabilitation'],
                ['Affordable housing', 'Basic amenities', 'Ownership rights'],
                ['Subsidized LPG', 'Clean cooking', 'Health benefits']
            ]
        }
    }
    
    template = scheme_templates[category]
    name = draw(st.sampled_from(template['names']))
    description = draw(st.sampled_from(template['descriptions']))
    benefits = draw(st.sampled_from(template['benefits']))
    
    departments = [
        'Ministry of Agriculture',
        'Ministry of Health',
        'Ministry of Education',
        'Ministry of Rural Development',
        'Ministry of Social Justice'
    ]
    
    states = [None, 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar']
    
    return {
        'scheme_id': uuid.uuid4(),
        'name': name,
        'category': category,
        'description': description,
        'benefits': benefits,
        'eligibility_criteria': draw(eligibility_criteria_strategy()),
        'required_documents': draw(st.lists(
            st.sampled_from(['Aadhaar Card', 'Income Certificate', 'Residence Proof', 'Bank Account']),
            min_size=1, max_size=4
        )),
        'application_process': draw(st.lists(
            st.sampled_from([
                'Visit official website',
                'Fill application form',
                'Upload documents',
                'Submit application',
                'Track status online'
            ]),
            min_size=2, max_size=5
        )),
        'application_url': f'https://example.gov.in/scheme/{uuid.uuid4()}',
        'department': draw(st.sampled_from(departments)),
        'state': draw(st.sampled_from(states)),
        'source_url': f'https://example.gov.in/source/{uuid.uuid4()}',
        'last_updated': datetime.utcnow(),
        'created_at': datetime.utcnow()
    }


# Strategy for generating search queries
@composite
def search_query_strategy(draw):
    """Generate search queries for schemes"""
    query_templates = {
        'agriculture': [
            'farmer assistance',
            'crop insurance',
            'agricultural support',
            'farming schemes',
            'kisan yojana',
            'soil health',
            'credit for farmers'
        ],
        'health': [
            'health insurance',
            'medical treatment',
            'healthcare schemes',
            'hospital coverage',
            'free medicine',
            'maternal health',
            'ayushman bharat'
        ],
        'education': [
            'student scholarship',
            'education support',
            'school meals',
            'learning programs',
            'skill training',
            'digital education'
        ],
        'employment': [
            'job opportunities',
            'employment guarantee',
            'self employment',
            'wage work',
            'rozgar yojana',
            'rural employment'
        ],
        'social_welfare': [
            'pension scheme',
            'widow support',
            'disability benefits',
            'housing scheme',
            'lpg subsidy',
            'social security'
        ]
    }
    
    category = draw(st.sampled_from(list(query_templates.keys())))
    query = draw(st.sampled_from(query_templates[category]))
    
    return query, category


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    # Need to handle UUID type for SQLite
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, ForeignKey
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
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
    
    # Create only scheme tables manually for SQLite compatibility
    from sqlalchemy import MetaData
    metadata = MetaData()
    
    schemes_table = Table(
        'schemes', metadata,
        Column('scheme_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('category', String(50), nullable=False),
        Column('description', Text, nullable=True),
        Column('benefits', JSON, nullable=True),
        Column('eligibility_criteria', JSON, nullable=False),
        Column('required_documents', JSON, nullable=True),
        Column('application_process', JSON, nullable=True),
        Column('application_url', String(500), nullable=True),
        Column('department', String(100), nullable=True),
        Column('state', String(50), nullable=True),
        Column('last_updated', DateTime, nullable=True),
        Column('source_url', String(500), nullable=True),
        Column('created_at', DateTime, nullable=False)
    )
    
    scheme_translations_table = Table(
        'scheme_translations', metadata,
        Column('translation_id', UUID(), primary_key=True),
        Column('scheme_id', UUID(), ForeignKey('schemes.scheme_id'), nullable=False),
        Column('language', String(10), nullable=False),
        Column('name', String(255), nullable=True),
        Column('description', Text, nullable=True),
        Column('benefits', JSON, nullable=True)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def add_schemes_to_db(session, schemes_data):
    """Helper to add schemes to test database"""
    # Clear existing schemes first to avoid accumulation
    session.query(Scheme).delete()
    session.commit()
    
    schemes = []
    for scheme_data in schemes_data:
        scheme = Scheme(**scheme_data)
        session.add(scheme)
        schemes.append(scheme)
    
    session.commit()
    return schemes


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=15),
    query_data=search_query_strategy()
)
def test_scheme_search_relevance_by_category(schemes, query_data, test_db_session):
    """
    Feature: bharatsahayak, Property 4: Scheme Search Relevance
    
    For any user query about government schemes, the System should retrieve 
    schemes where the category matches the query context.
    
    This tests that category-based filtering works correctly.
    """
    query, expected_category = query_data
    
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Create repository and search
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category=expected_category)
    results = repository.search_schemes(filters, limit=100)
    
    # Property 1: All returned schemes should match the category
    for scheme in results:
        assert scheme.category == expected_category, \
            f"Scheme category '{scheme.category}' should match expected '{expected_category}'"
    
    # Property 2: Should return all schemes of that category
    expected_count = sum(1 for s in schemes if s['category'] == expected_category)
    assert len(results) == expected_count, \
        f"Should return {expected_count} schemes, got {len(results)}"


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=15),
    search_term=st.text(min_size=3, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll')
    ))
)
def test_scheme_search_relevance_by_text(schemes, search_term, test_db_session):
    """
    Feature: bharatsahayak, Property 4: Scheme Search Relevance
    
    For any text search query, the System should retrieve schemes where 
    the name or description contains the search term.
    
    This tests text-based search functionality.
    """
    assume(len(search_term.strip()) >= 3)
    
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Create repository and search
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(query=search_term)
    results = repository.search_schemes(filters, limit=100)
    
    # Property: All returned schemes should contain the search term in name or description
    search_lower = search_term.lower()
    for scheme in results:
        name_match = search_lower in scheme.name.lower()
        desc_match = scheme.description and search_lower in scheme.description.lower()
        
        assert name_match or desc_match, \
            f"Scheme should contain '{search_term}' in name or description"


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=15),
    state=st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar'])
)
def test_scheme_search_relevance_by_state(schemes, state, test_db_session):
    """
    Feature: bharatsahayak, Property 4: Scheme Search Relevance
    
    For any state-based query, the System should retrieve schemes 
    applicable to that state (including central schemes).
    
    This tests location-based filtering.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Create repository and search
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(state=state)
    results = repository.search_schemes(filters, limit=100)
    
    # Property: All returned schemes should be for the state or be central schemes (state=None)
    for scheme in results:
        assert scheme.state == state or scheme.state is None, \
            f"Scheme should be for state '{state}' or be a central scheme (None)"
    
    # Property: Should include all state-specific and central schemes
    expected_schemes = [
        s for s in schemes 
        if s['state'] == state or s['state'] is None
    ]
    assert len(results) == len(expected_schemes), \
        f"Should return {len(expected_schemes)} schemes, got {len(results)}"


@settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=15),
    category=st.sampled_from(['agriculture', 'health', 'education', 'employment', 'social_welfare']),
    state=st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', None])
)
def test_scheme_search_relevance_combined_filters(schemes, category, state, test_db_session):
    """
    Feature: bharatsahayak, Property 4: Scheme Search Relevance
    
    For any query with multiple filters, the System should retrieve schemes 
    that match ALL specified criteria.
    
    This tests combined filter functionality.
    """
    # Add schemes to database
    add_schemes_to_db(test_db_session, schemes)
    
    # Create repository and search with combined filters
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category=category, state=state)
    results = repository.search_schemes(filters, limit=100)
    
    # Property: All returned schemes should match both category and state filters
    for scheme in results:
        assert scheme.category == category, \
            f"Scheme category should be '{category}'"
        
        if state is not None:
            assert scheme.state == state or scheme.state is None, \
                f"Scheme should be for state '{state}' or be central"
        else:
            # If state filter is None, should return all schemes of that category
            pass
    
    # Property: Should return correct count
    if state is not None:
        expected_schemes = [
            s for s in schemes 
            if s['category'] == category and (s['state'] == state or s['state'] is None)
        ]
    else:
        expected_schemes = [
            s for s in schemes 
            if s['category'] == category
        ]
    
    assert len(results) == len(expected_schemes), \
        f"Should return {len(expected_schemes)} schemes, got {len(results)}"


def test_scheme_search_specific_farmer_query(test_db_session):
    """
    Specific example test: Query for farmer schemes should return agriculture schemes.
    
    This complements property-based tests with a concrete example.
    """
    # Create specific schemes
    schemes_data = [
        {
            'scheme_id': uuid.uuid4(),
            'name': 'PM-KISAN Scheme',
            'category': 'agriculture',
            'description': 'Provides Rs 6000 per year to farmers',
            'benefits': ['Direct income support', 'Financial assistance'],
            'eligibility_criteria': {'occupation': ['Farmer']},
            'required_documents': ['Aadhaar', 'Land records'],
            'application_process': ['Visit website', 'Apply online'],
            'application_url': 'https://pmkisan.gov.in',
            'department': 'Ministry of Agriculture',
            'state': None,
            'source_url': 'https://pmkisan.gov.in',
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        },
        {
            'scheme_id': uuid.uuid4(),
            'name': 'Ayushman Bharat',
            'category': 'health',
            'description': 'Health insurance for poor families',
            'benefits': ['Rs 5 lakh coverage', 'Cashless treatment'],
            'eligibility_criteria': {'income_max': 100000},
            'required_documents': ['Aadhaar', 'Income certificate'],
            'application_process': ['Visit hospital', 'Get card'],
            'application_url': 'https://pmjay.gov.in',
            'department': 'Ministry of Health',
            'state': None,
            'source_url': 'https://pmjay.gov.in',
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    ]
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    # Search for farmer schemes
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(query='farmer')
    results = repository.search_schemes(filters)
    
    # Should find PM-KISAN
    assert len(results) > 0, "Should find schemes related to farmers"
    
    found_pmkisan = False
    for scheme in results:
        if 'PM-KISAN' in scheme.name or 'farmer' in scheme.description.lower():
            found_pmkisan = True
            break
    
    assert found_pmkisan, "Should find PM-KISAN scheme for farmer query"


def test_scheme_search_specific_health_query(test_db_session):
    """
    Specific example test: Query for health schemes should return health category.
    """
    schemes_data = [
        {
            'scheme_id': uuid.uuid4(),
            'name': 'Ayushman Bharat',
            'category': 'health',
            'description': 'Health insurance for poor families',
            'benefits': ['Rs 5 lakh coverage'],
            'eligibility_criteria': {},
            'required_documents': ['Aadhaar'],
            'application_process': ['Apply online'],
            'application_url': 'https://pmjay.gov.in',
            'department': 'Ministry of Health',
            'state': None,
            'source_url': 'https://pmjay.gov.in',
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        },
        {
            'scheme_id': uuid.uuid4(),
            'name': 'Crop Insurance',
            'category': 'agriculture',
            'description': 'Insurance for crop losses',
            'benefits': ['Risk coverage'],
            'eligibility_criteria': {},
            'required_documents': ['Land records'],
            'application_process': ['Apply through bank'],
            'application_url': 'https://pmfby.gov.in',
            'department': 'Ministry of Agriculture',
            'state': None,
            'source_url': 'https://pmfby.gov.in',
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    ]
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    # Search by health category
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category='health')
    results = repository.search_schemes(filters)
    
    # Should only return health schemes
    assert len(results) == 1, "Should find exactly one health scheme"
    assert results[0].category == 'health', "Result should be health category"
    assert 'Ayushman' in results[0].name, "Should find Ayushman Bharat"


def test_scheme_search_no_results(test_db_session):
    """
    Edge case test: Query with no matching schemes should return empty list.
    """
    schemes_data = [
        {
            'scheme_id': uuid.uuid4(),
            'name': 'PM-KISAN',
            'category': 'agriculture',
            'description': 'Farmer support scheme',
            'benefits': ['Income support'],
            'eligibility_criteria': {},
            'required_documents': [],
            'application_process': [],
            'application_url': None,
            'department': 'Agriculture',
            'state': None,
            'source_url': None,
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    ]
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    # Search for non-existent category
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category='nonexistent')
    results = repository.search_schemes(filters)
    
    # Should return empty list
    assert len(results) == 0, "Should return no results for non-existent category"
    assert isinstance(results, list), "Should return a list"


def test_scheme_search_pagination(test_db_session):
    """
    Test that pagination works correctly for scheme search.
    """
    # Create 10 schemes
    schemes_data = []
    for i in range(10):
        schemes_data.append({
            'scheme_id': uuid.uuid4(),
            'name': f'Scheme {i}',
            'category': 'agriculture',
            'description': f'Description {i}',
            'benefits': [f'Benefit {i}'],
            'eligibility_criteria': {},
            'required_documents': [],
            'application_process': [],
            'application_url': None,
            'department': 'Agriculture',
            'state': None,
            'source_url': None,
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        })
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category='agriculture')
    
    # Get first page
    page1 = repository.search_schemes(filters, limit=5, offset=0)
    assert len(page1) == 5, "First page should have 5 results"
    
    # Get second page
    page2 = repository.search_schemes(filters, limit=5, offset=5)
    assert len(page2) == 5, "Second page should have 5 results"
    
    # Pages should not overlap
    page1_ids = {str(s.scheme_id) for s in page1}
    page2_ids = {str(s.scheme_id) for s in page2}
    assert len(page1_ids & page2_ids) == 0, "Pages should not have overlapping schemes"


def test_scheme_search_ordering(test_db_session):
    """
    Test that schemes are ordered by created_at descending (newest first).
    """
    import time
    
    schemes_data = []
    for i in range(5):
        schemes_data.append({
            'scheme_id': uuid.uuid4(),
            'name': f'Scheme {i}',
            'category': 'agriculture',
            'description': f'Description {i}',
            'benefits': [],
            'eligibility_criteria': {},
            'required_documents': [],
            'application_process': [],
            'application_url': None,
            'department': 'Agriculture',
            'state': None,
            'source_url': None,
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        })
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    repository = SchemeRepository(test_db_session)
    filters = SchemeFilters(category='agriculture')
    results = repository.search_schemes(filters)
    
    # Should be ordered by created_at descending
    for i in range(len(results) - 1):
        assert results[i].created_at >= results[i+1].created_at, \
            "Results should be ordered by created_at descending"


def test_scheme_search_case_insensitive(test_db_session):
    """
    Test that text search is case-insensitive.
    """
    schemes_data = [
        {
            'scheme_id': uuid.uuid4(),
            'name': 'PM-KISAN Scheme',
            'category': 'agriculture',
            'description': 'Provides support to FARMERS',
            'benefits': [],
            'eligibility_criteria': {},
            'required_documents': [],
            'application_process': [],
            'application_url': None,
            'department': 'Agriculture',
            'state': None,
            'source_url': None,
            'last_updated': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
    ]
    
    add_schemes_to_db(test_db_session, schemes_data)
    
    repository = SchemeRepository(test_db_session)
    
    # Search with lowercase
    filters1 = SchemeFilters(query='farmer')
    results1 = repository.search_schemes(filters1)
    
    # Search with uppercase
    filters2 = SchemeFilters(query='FARMER')
    results2 = repository.search_schemes(filters2)
    
    # Search with mixed case
    filters3 = SchemeFilters(query='FaRmEr')
    results3 = repository.search_schemes(filters3)
    
    # All should return the same result
    assert len(results1) == 1, "Lowercase search should find scheme"
    assert len(results2) == 1, "Uppercase search should find scheme"
    assert len(results3) == 1, "Mixed case search should find scheme"
    
    assert results1[0].scheme_id == results2[0].scheme_id == results3[0].scheme_id, \
        "All searches should find the same scheme"
