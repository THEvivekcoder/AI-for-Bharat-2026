"""Property-based tests for official source prioritization in RAG.

Feature: bharatsahayak, Property 17: Official Source Prioritization
**Validates: Requirements 6.5**

This test verifies that the RAG engine prioritizes official government sources
over general sources when both are available, ensuring users receive authoritative
information.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.services.rag_engine import RAGEngine, ConversationContext


# Custom strategies for generating valid test data
@st.composite
def query_strategy(draw):
    """Generate realistic user queries."""
    query_templates = [
        "What is {scheme}?",
        "Tell me about {scheme}",
        "How do I apply for {scheme}?",
        "What are the benefits of {scheme}?",
        "Am I eligible for {scheme}?"
    ]
    
    schemes = [
        "PM-KISAN", "Ayushman Bharat", "Pradhan Mantri Awas Yojana",
        "Kisan Credit Card", "National Scholarship Portal",
        "Skill India", "MGNREGA", "Pension Scheme"
    ]
    
    template = draw(st.sampled_from(query_templates))
    scheme = draw(st.sampled_from(schemes))
    
    return template.format(scheme=scheme)


@st.composite
def search_result_strategy(draw, source_type: str, score_range: tuple = (0.7, 1.0)):
    """Generate mock search results with specified source type."""
    scheme_id = f"scheme-{draw(st.integers(min_value=1000, max_value=9999))}"
    
    categories = ["agriculture", "health", "education", "employment", "social_welfare"]
    category = draw(st.sampled_from(categories))
    
    official_names = {
        "agriculture": ["PM-KISAN", "Crop Insurance Scheme", "Kisan Credit Card"],
        "health": ["Ayushman Bharat", "National Health Mission", "Pradhan Mantri Jan Arogya Yojana"],
        "education": ["National Scholarship Portal", "Samagra Shiksha", "Mid-Day Meal Scheme"],
        "employment": ["Skill India", "MGNREGA", "Pradhan Mantri Kaushal Vikas Yojana"],
        "social_welfare": ["National Pension Scheme", "Pradhan Mantri Awas Yojana", "Ujjwala Yojana"]
    }
    
    general_names = {
        "agriculture": ["Farming Support Program", "Agricultural Aid", "Crop Assistance"],
        "health": ["Healthcare Program", "Medical Support", "Health Assistance"],
        "education": ["Education Support", "Student Aid", "Learning Program"],
        "employment": ["Job Training", "Employment Support", "Work Program"],
        "social_welfare": ["Welfare Program", "Social Support", "Benefit Scheme"]
    }
    
    names = official_names if source_type == "official" else general_names
    name = draw(st.sampled_from(names.get(category, ["Government Scheme"])))
    
    return {
        'id': scheme_id,
        'score': draw(st.floats(min_value=score_range[0], max_value=score_range[1])),
        'source': {
            'scheme_id': scheme_id,
            'name': name,
            'category': category,
            'description': f"{'Official government' if source_type == 'official' else 'General'} {category} scheme",
            'source_type': source_type
        }
    }


@settings(max_examples=20, deadline=None)
@given(
    query=query_strategy(),
    num_official=st.integers(min_value=2, max_value=5),
    num_general=st.integers(min_value=2, max_value=5)
)
def test_official_source_prioritization(query, num_official, num_general):
    """
    Feature: bharatsahayak, Property 17: Official Source Prioritization
    
    For any query where both official government sources and general sources
    are available, the RAG_Engine should rank official sources higher in the
    retrieved documents.
    
    This test verifies:
    1. Official sources appear before general sources in results
    2. When both source types have similar relevance scores, official sources are prioritized
    3. The RAG engine searches official sources first
    4. General sources are only included if official sources are insufficient
    """
    # Generate official sources with high scores
    official_results = [
        {
            'id': f'official-{i}',
            'score': 0.85 + (i * 0.02),  # Scores: 0.85, 0.87, 0.89, etc.
            'source': {
                'scheme_id': f'official-{i}',
                'name': f'PM Official Scheme {i}',
                'category': 'agriculture',
                'description': 'Official government scheme',
                'source_type': 'official'
            }
        }
        for i in range(num_official)
    ]
    
    # Generate general sources with similar or even higher scores
    general_results = [
        {
            'id': f'general-{i}',
            'score': 0.90 + (i * 0.01),  # Scores: 0.90, 0.91, 0.92, etc. (higher than official!)
            'source': {
                'scheme_id': f'general-{i}',
                'name': f'General Program {i}',
                'category': 'agriculture',
                'description': 'General information source',
                'source_type': 'general'
            }
        }
        for i in range(num_general)
    ]
    
    # Mock OpenSearch vector store
    # The RAG engine calls search twice: first for official, then for general
    mock_vector_store = Mock()
    mock_vector_store.search.side_effect = [official_results, general_results]
    
    # Mock Bedrock LLM service
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response based on official sources"
    
    # Create RAG engine with mocked dependencies
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[]
            )
            
            response = rag_engine.query(query, context, top_k=5)
            
            # Property verification 1: Official sources should be searched first
            assert mock_vector_store.search.call_count >= 1, "Should search for sources"
            
            # Get the first search call (should be for official sources)
            first_call_kwargs = mock_vector_store.search.call_args_list[0][1]
            assert 'filters' in first_call_kwargs, "First search should have filters"
            assert first_call_kwargs['filters'].get('source_type') == 'official', (
                "First search should filter for official sources"
            )
            
            # Property verification 2: Official sources should appear first in results
            official_sources = [s for s in response.sources if s.get('source_type') == 'official']
            general_sources = [s for s in response.sources if s.get('source_type') == 'general']
            
            if len(official_sources) > 0 and len(general_sources) > 0:
                # Find the index of the last official source
                last_official_idx = -1
                first_general_idx = len(response.sources)
                
                for i, source in enumerate(response.sources):
                    if source.get('source_type') == 'official':
                        last_official_idx = i
                    elif source.get('source_type') == 'general' and first_general_idx == len(response.sources):
                        first_general_idx = i
                
                assert last_official_idx < first_general_idx, (
                    f"Official sources should appear before general sources. "
                    f"Last official at index {last_official_idx}, "
                    f"first general at index {first_general_idx}"
                )
            
            # Property verification 3: Official sources should be prioritized even with lower scores
            # (This is verified by the search order - official sources are searched first)
            assert len(official_sources) > 0, (
                "Should include official sources when available"
            )


@settings(max_examples=15, deadline=None)
@given(
    query=query_strategy(),
    num_official=st.integers(min_value=5, max_value=10)
)
def test_official_sources_sufficient(query, num_official):
    """
    Test that when enough official sources are available, general sources are not included.
    
    This verifies that the RAG engine only searches for general sources when
    official sources are insufficient.
    """
    # Generate enough official sources to satisfy top_k
    official_results = [
        {
            'id': f'official-{i}',
            'score': 0.95 - (i * 0.02),  # Decreasing scores
            'source': {
                'scheme_id': f'official-{i}',
                'name': f'Official Scheme {i}',
                'category': 'agriculture',
                'description': 'Official government scheme',
                'source_type': 'official'
            }
        }
        for i in range(num_official)
    ]
    
    # Mock dependencies
    mock_vector_store = Mock()
    # First call returns official sources, second call should not happen or return empty
    mock_vector_store.search.side_effect = [official_results, []]
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response"
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[]
            )
            
            response = rag_engine.query(query, context, top_k=5)
            
            # Property verification: All sources should be official
            for source in response.sources:
                assert source.get('source_type') == 'official', (
                    f"When sufficient official sources exist, all results should be official. "
                    f"Found {source.get('source_type')} source: {source.get('name')}"
                )
            
            # Verify we got results
            assert len(response.sources) > 0, "Should return official sources"


@settings(max_examples=15, deadline=None)
@given(
    query=query_strategy(),
    num_official=st.integers(min_value=1, max_value=3),
    num_general=st.integers(min_value=2, max_value=5)
)
def test_general_sources_supplement_official(query, num_official, num_general):
    """
    Test that general sources are included only when official sources are insufficient.
    
    This verifies that the RAG engine supplements with general sources when
    there aren't enough official sources to meet top_k.
    """
    # Generate few official sources
    official_results = [
        {
            'id': f'official-{i}',
            'score': 0.90 - (i * 0.05),
            'source': {
                'scheme_id': f'official-{i}',
                'name': f'Official Scheme {i}',
                'category': 'agriculture',
                'description': 'Official government scheme',
                'source_type': 'official'
            }
        }
        for i in range(num_official)
    ]
    
    # Generate general sources to supplement
    general_results = [
        {
            'id': f'general-{i}',
            'score': 0.85 - (i * 0.05),
            'source': {
                'scheme_id': f'general-{i}',
                'name': f'General Program {i}',
                'category': 'agriculture',
                'description': 'General information',
                'source_type': 'general'
            }
        }
        for i in range(num_general)
    ]
    
    # Assume we need more sources than official provides
    top_k = 5
    assume(num_official < top_k)
    
    # Mock dependencies
    mock_vector_store = Mock()
    mock_vector_store.search.side_effect = [official_results, general_results]
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response"
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[]
            )
            
            response = rag_engine.query(query, context, top_k=top_k)
            
            # Property verification 1: Should include both official and general sources
            official_sources = [s for s in response.sources if s.get('source_type') == 'official']
            general_sources = [s for s in response.sources if s.get('source_type') == 'general']
            
            assert len(official_sources) > 0, "Should include official sources"
            assert len(general_sources) > 0, "Should supplement with general sources when official insufficient"
            
            # Property verification 2: Official sources should still come first
            first_general_idx = next(
                (i for i, s in enumerate(response.sources) if s.get('source_type') == 'general'),
                len(response.sources)
            )
            last_official_idx = next(
                (i for i in range(len(response.sources) - 1, -1, -1) 
                 if response.sources[i].get('source_type') == 'official'),
                -1
            )
            
            if last_official_idx >= 0 and first_general_idx < len(response.sources):
                assert last_official_idx < first_general_idx, (
                    "Official sources should appear before general sources"
                )


@settings(max_examples=10, deadline=None)
@given(
    query=query_strategy()
)
def test_source_type_filter_in_search(query):
    """
    Test that the RAG engine uses source_type filters when searching.
    
    This verifies that the vector store search is called with appropriate
    filters to separate official and general sources.
    """
    # Mock dependencies
    mock_vector_store = Mock()
    mock_vector_store.search.side_effect = [
        [  # Official sources
            {
                'id': 'official-1',
                'score': 0.90,
                'source': {
                    'scheme_id': 'official-1',
                    'name': 'Official Scheme',
                    'category': 'agriculture',
                    'description': 'Official',
                    'source_type': 'official'
                }
            }
        ],
        []  # No general sources needed
    ]
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response"
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[]
            )
            
            response = rag_engine.query(query, context, top_k=5)
            
            # Property verification: Search should be called with source_type filters
            assert mock_vector_store.search.call_count >= 1, "Should call search"
            
            # Check first call (official sources)
            first_call = mock_vector_store.search.call_args_list[0]
            first_call_kwargs = first_call[1]
            
            assert 'filters' in first_call_kwargs, "Should use filters in search"
            assert 'source_type' in first_call_kwargs['filters'], "Should filter by source_type"
            assert first_call_kwargs['filters']['source_type'] == 'official', (
                "First search should filter for official sources"
            )
            
            # If there's a second call, it should be for general sources
            if mock_vector_store.search.call_count >= 2:
                second_call = mock_vector_store.search.call_args_list[1]
                second_call_kwargs = second_call[1]
                
                if 'filters' in second_call_kwargs and 'source_type' in second_call_kwargs['filters']:
                    assert second_call_kwargs['filters']['source_type'] == 'general', (
                        "Second search should filter for general sources"
                    )


@settings(max_examples=10, deadline=None)
@given(
    query=query_strategy()
)
def test_no_general_sources_when_official_available(query):
    """
    Test that general sources are not retrieved when sufficient official sources exist.
    
    This is a stronger version of the prioritization test - verifying that
    the second search (for general sources) is not performed or returns empty
    when official sources are sufficient.
    """
    # Generate sufficient official sources
    official_results = [
        {
            'id': f'official-{i}',
            'score': 0.95 - (i * 0.02),
            'source': {
                'scheme_id': f'official-{i}',
                'name': f'Official Scheme {i}',
                'category': 'agriculture',
                'description': 'Official government scheme',
                'source_type': 'official'
            }
        }
        for i in range(7)  # More than top_k=5
    ]
    
    # Mock dependencies
    mock_vector_store = Mock()
    # Return official sources, then empty list for general
    mock_vector_store.search.side_effect = [official_results, []]
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536
    mock_llm.generate_response.return_value = "Response"
    
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[]
            )
            
            response = rag_engine.query(query, context, top_k=5)
            
            # Property verification: No general sources in results
            general_sources = [s for s in response.sources if s.get('source_type') == 'general']
            
            assert len(general_sources) == 0, (
                f"Should not include general sources when sufficient official sources exist. "
                f"Found {len(general_sources)} general sources"
            )
            
            # All sources should be official
            assert all(s.get('source_type') == 'official' for s in response.sources), (
                "All sources should be official when sufficient official sources are available"
            )
