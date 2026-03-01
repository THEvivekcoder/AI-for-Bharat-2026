"""Property-based tests for scheme search relevance.

Feature: bharatsahayak, Property 4: Scheme Search Relevance
**Validates: Requirements 2.1**

This test verifies that search results match query context semantically,
ensuring that returned schemes are relevant to the user's search intent.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck
from datetime import datetime
from unittest.mock import Mock, patch
from typing import List

from src.core.scheme_repository import SchemeRepository, SchemeFilters
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria


# Custom strategies for generating valid test data
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
    
    # Generate scheme name and description based on category
    category_keywords = {
        "agriculture": ["farmer", "crop", "irrigation", "fertilizer", "kisan", "krishi"],
        "health": ["health", "medical", "insurance", "hospital", "treatment", "ayushman"],
        "education": ["education", "scholarship", "student", "school", "college", "vidya"],
        "employment": ["job", "employment", "skill", "training", "rozgar", "kaushal"],
        "social_welfare": ["welfare", "pension", "widow", "disability", "senior citizen"]
    }
    
    # Select keywords for this category
    cat_keywords = category_keywords.get(selected_category, ["scheme", "benefit"])
    name_keyword = draw(st.sampled_from(cat_keywords))
    desc_keyword = draw(st.sampled_from(cat_keywords))
    
    scheme_id = f"{selected_category.upper()[:3]}-{draw(st.integers(min_value=1000, max_value=9999))}"
    name = f"{name_keyword.title()} {draw(st.sampled_from(['Scheme', 'Yojana', 'Program', 'Initiative']))}"
    description = f"This scheme provides {desc_keyword} support to eligible beneficiaries"
    
    departments = {
        "agriculture": "Ministry of Agriculture and Farmers Welfare",
        "health": "Ministry of Health and Family Welfare",
        "education": "Ministry of Education",
        "employment": "Ministry of Labour and Employment",
        "social_welfare": "Ministry of Social Justice and Empowerment"
    }
    
    return Scheme(
        scheme_id=scheme_id,
        name=name,
        name_translations={},
        category=selected_category,
        description=description,
        description_translations={},
        benefits=draw(st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=5)),
        eligibility_criteria=draw(eligibility_criteria_strategy()),
        required_documents=draw(st.lists(
            st.sampled_from(["Aadhaar", "PAN", "Income Certificate", "Caste Certificate"]),
            min_size=1, max_size=4
        )),
        application_process=draw(st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=5)),
        application_url=f"https://example.gov.in/{scheme_id.lower()}",
        department=departments.get(selected_category, "Government Department"),
        state=draw(st.none() | st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", None])),
        last_updated=datetime(2024, 1, 15, 10, 30, 0),
        source_url=f"https://example.gov.in/source/{scheme_id.lower()}"
    )


def contains_keyword_case_insensitive(text: str, keyword: str) -> bool:
    """Check if text contains keyword (case-insensitive)."""
    return keyword.lower() in text.lower()


def scheme_matches_query(scheme: Scheme, query: str) -> bool:
    """
    Determine if a scheme semantically matches a query.
    
    A scheme matches if the query keyword appears in:
    - Scheme name
    - Scheme description
    - Scheme category (if query is a category name)
    """
    query_lower = query.lower()
    
    # Check name
    if contains_keyword_case_insensitive(scheme.name, query):
        return True
    
    # Check description
    if contains_keyword_case_insensitive(scheme.description, query):
        return True
    
    # Check category match
    if query_lower == scheme.category.lower():
        return True
    
    # Check if query is a common synonym for the category
    category_synonyms = {
        "agriculture": ["farm", "farmer", "crop", "kisan", "krishi"],
        "health": ["medical", "hospital", "treatment", "doctor", "ayushman"],
        "education": ["school", "college", "student", "scholarship", "vidya"],
        "employment": ["job", "work", "skill", "training", "rozgar"],
        "social_welfare": ["welfare", "pension", "benefit"]
    }
    
    for category, synonyms in category_synonyms.items():
        if scheme.category == category and query_lower in synonyms:
            return True
    
    return False


@settings(max_examples=20, deadline=None)
@given(
    query=st.sampled_from([
        "farmer", "crop", "agriculture", "kisan",
        "health", "medical", "insurance", "ayushman",
        "education", "scholarship", "student",
        "job", "employment", "skill", "training",
        "pension", "welfare"
    ]),
    schemes=st.lists(scheme_strategy(), min_size=5, max_size=20)
)
def test_scheme_search_relevance(query, schemes):
    """
    Feature: bharatsahayak, Property 4: Scheme Search Relevance
    
    For any user query about government schemes, the System should retrieve
    schemes from the Scheme_Database where the scheme description, category,
    or benefits semantically match the query context.
    
    This test verifies:
    1. All returned schemes contain the query keyword in name, description, or category
    2. Schemes that match the query are not excluded from results
    3. Search is case-insensitive
    4. Category-based queries return schemes from that category
    """
    # Filter schemes that should match the query
    matching_schemes = [s for s in schemes if scheme_matches_query(s, query)]
    
    # Ensure we have at least one matching scheme
    assume(len(matching_schemes) > 0)
    
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = SchemeRepository(table_name="TestSchemes")
            repo.table = mock_table
            
            # Convert schemes to DynamoDB format
            scheme_items = []
            for scheme in matching_schemes:
                scheme_dict = scheme.model_dump()
                scheme_dict['last_updated'] = scheme.last_updated.isoformat()
                scheme_items.append(scheme_dict)
            
            mock_table.scan.return_value = {'Items': scheme_items}
            mock_table.query.return_value = {'Items': scheme_items}
            
            # Perform search
            results = repo.search_schemes(query=query, limit=50)
            
            # Property verification: All returned schemes should match the query
            assert len(results) > 0, f"Search for '{query}' should return at least one scheme"
            
            for scheme in results:
                matches = scheme_matches_query(scheme, query)
                assert matches, (
                    f"Scheme '{scheme.name}' (category: {scheme.category}) "
                    f"does not match query '{query}'. "
                    f"Description: {scheme.description[:100]}"
                )
            
            # Verify that we didn't miss any matching schemes
            result_ids = {s.scheme_id for s in results}
            expected_ids = {s.scheme_id for s in matching_schemes}
            assert result_ids == expected_ids, (
                f"Search results don't match expected schemes. "
                f"Missing: {expected_ids - result_ids}, "
                f"Extra: {result_ids - expected_ids}"
            )


@settings(max_examples=10, deadline=None)
@given(
    category=st.sampled_from(["agriculture", "health", "education", "employment", "social_welfare"]),
    schemes=st.lists(scheme_strategy(), min_size=3, max_size=15)
)
def test_category_filter_relevance(category, schemes):
    """
    Test that category filtering returns only schemes from that category.
    
    This is a specific case of search relevance where the filter is explicit.
    """
    # Filter schemes by category
    filtered_schemes = [s for s in schemes if s.category == category]
    
    # Ensure we have at least one scheme in the target category
    assume(len(filtered_schemes) > 0)
    
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = SchemeRepository(table_name="TestSchemes")
            repo.table = mock_table
            
            # Convert to DynamoDB format
            scheme_items = []
            for scheme in filtered_schemes:
                scheme_dict = scheme.model_dump()
                scheme_dict['last_updated'] = scheme.last_updated.isoformat()
                scheme_items.append(scheme_dict)
            
            mock_table.query.return_value = {'Items': scheme_items}
            
            # Perform search with category filter
            filters = SchemeFilters(category=category)
            results = repo.search_schemes(filters=filters, limit=50)
            
            # Verify all results are from the specified category
            assert len(results) > 0, f"Should return at least one scheme for category '{category}'"
            
            for scheme in results:
                assert scheme.category == category, (
                    f"Scheme '{scheme.name}' has category '{scheme.category}' "
                    f"but filter was for '{category}'"
                )


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.data_too_large])
@given(
    query=st.sampled_from([
        "farmer", "crop", "agriculture",
        "health", "medical", "insurance",
        "education", "scholarship", "student",
        "job", "employment", "skill",
        "pension", "welfare"
    ]),
    category=st.sampled_from(["agriculture", "health", "education", "employment", "social_welfare"]),
    schemes=st.lists(scheme_strategy(), min_size=3, max_size=10)
)
def test_combined_query_and_category_filter(query, category, schemes):
    """
    Test that combining keyword search with category filter returns relevant results.
    
    Results should match both the query AND the category filter.
    """
    # Filter schemes by both query and category
    filtered_schemes = [
        s for s in schemes
        if s.category == category and scheme_matches_query(s, query)
    ]
    
    # Skip test if no schemes match both criteria
    assume(len(filtered_schemes) > 0)
    
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = SchemeRepository(table_name="TestSchemes")
            repo.table = mock_table
            
            # Convert to DynamoDB format
            scheme_items = []
            for scheme in filtered_schemes:
                scheme_dict = scheme.model_dump()
                scheme_dict['last_updated'] = scheme.last_updated.isoformat()
                scheme_items.append(scheme_dict)
            
            mock_table.query.return_value = {'Items': scheme_items}
            
            # Perform search with both query and category filter
            filters = SchemeFilters(category=category)
            results = repo.search_schemes(query=query, filters=filters, limit=50)
            
            # Verify all results match both criteria
            for scheme in results:
                assert scheme.category == category, (
                    f"Scheme '{scheme.name}' has wrong category"
                )
                assert scheme_matches_query(scheme, query), (
                    f"Scheme '{scheme.name}' doesn't match query '{query}'"
                )
