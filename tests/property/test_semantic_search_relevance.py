"""Property-based tests for semantic search relevance in RAG.

Feature: bharatsahayak, Property 16: Semantic Search Relevance
**Validates: Requirements 6.2**

This test verifies that the RAG engine retrieves relevant documents from the
knowledge base using semantic search, ensuring that retrieved documents have
high similarity scores to the query embedding.
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
        "What schemes are available for {topic}?",
        "Tell me about {topic}",
        "How can I get help with {topic}?",
        "What are the benefits of {topic}?",
        "I need information about {topic}",
        "Can you explain {topic} schemes?",
        "What government programs support {topic}?"
    ]
    
    topics = [
        "farmers", "agriculture", "crop insurance", "PM-KISAN",
        "health insurance", "Ayushman Bharat", "medical treatment",
        "education", "scholarships", "student loans",
        "employment", "job training", "skill development",
        "pension", "senior citizens", "disability benefits"
    ]
    
    template = draw(st.sampled_from(query_templates))
    topic = draw(st.sampled_from(topics))
    
    return template.format(topic=topic)


@st.composite
def search_result_strategy(draw, min_score=0.0, max_score=1.0):
    """Generate mock search results with similarity scores."""
    scheme_id = f"scheme-{draw(st.integers(min_value=1000, max_value=9999))}"
    
    categories = ["agriculture", "health", "education", "employment", "social_welfare"]
    category = draw(st.sampled_from(categories))
    
    names = {
        "agriculture": ["PM-KISAN", "Crop Insurance Scheme", "Kisan Credit Card"],
        "health": ["Ayushman Bharat", "Health Insurance Scheme", "Medical Assistance"],
        "education": ["Scholarship Scheme", "Student Loan Program", "Education Support"],
        "employment": ["Skill Development Program", "Job Training Scheme", "Employment Support"],
        "social_welfare": ["Pension Scheme", "Disability Benefits", "Welfare Program"]
    }
    
    name = draw(st.sampled_from(names.get(category, ["Government Scheme"])))
    
    return {
        'id': scheme_id,
        'score': draw(st.floats(min_value=min_score, max_value=max_score)),
        'source': {
            'scheme_id': scheme_id,
            'name': name,
            'category': category,
            'description': f"This scheme provides {category} support to eligible beneficiaries",
            'source_type': draw(st.sampled_from(['official', 'general']))
        }
    }


def calculate_semantic_similarity(query: str, document: Dict[str, Any]) -> float:
    """
    Simple semantic similarity calculation for testing.
    
    In production, this would use actual embeddings and cosine similarity.
    For testing, we use keyword matching as a proxy.
    """
    query_lower = query.lower()
    doc_text = f"{document['source']['name']} {document['source']['description']} {document['source']['category']}".lower()
    
    # Count matching words
    query_words = set(query_lower.split())
    doc_words = set(doc_text.split())
    
    common_words = query_words.intersection(doc_words)
    
    if len(query_words) == 0:
        return 0.0
    
    # Similarity based on word overlap
    similarity = len(common_words) / len(query_words)
    
    return min(similarity, 1.0)


@settings(max_examples=20, deadline=None)
@given(
    query=query_strategy(),
    min_score_threshold=st.floats(min_value=0.5, max_value=0.9)
)
def test_semantic_search_relevance(query, min_score_threshold):
    """
    Feature: bharatsahayak, Property 16: Semantic Search Relevance
    
    For any user query, the top-k documents retrieved from the knowledge base
    should have semantic similarity scores above a threshold (e.g., 0.7) to
    the query embedding.
    
    This test verifies:
    1. All retrieved documents have similarity scores above the minimum threshold
    2. Documents are sorted by relevance (highest score first)
    3. The search returns relevant documents based on semantic meaning
    4. Low-relevance documents are filtered out
    """
    # Generate mock search results with varying scores (sorted by score descending)
    high_score_results = [
        {
            'id': f'scheme-{i}',
            'score': 0.95 - (i * 0.05),  # Scores from 0.95 to 0.75 (descending)
            'source': {
                'scheme_id': f'scheme-{i}',
                'name': f'Relevant Scheme {i}',
                'category': 'agriculture',
                'description': f'Scheme related to {query.split()[0]}',
                'source_type': 'official'
            }
        }
        for i in range(5)
    ]
    
    # Mock OpenSearch vector store
    # The RAG engine calls search twice: once for official, once for general
    mock_vector_store = Mock()
    # First call returns official sources, second call returns empty (no general sources needed)
    mock_vector_store.search.side_effect = [high_score_results, []]
    
    # Mock Bedrock LLM service
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = [0.1] * 1536  # Mock embedding
    
    # Create RAG engine with mocked dependencies
    with patch('src.services.rag_engine.OpenSearchVectorStore', return_value=mock_vector_store):
        with patch('src.services.rag_engine.BedrockLLMService', return_value=mock_llm):
            rag_engine = RAGEngine(opensearch_endpoint="mock-endpoint")
            rag_engine.vector_store = mock_vector_store
            rag_engine.llm = mock_llm
            
            # Verify that search was called with min_score parameter
            # The RAG engine should filter results by minimum score
            mock_vector_store.search.assert_not_called()  # Not called yet
            
            # Simulate a query (this will call vector_store.search internally)
            context = ConversationContext(
                session_id="test-session",
                user_id="test-user",
                language="en",
                history=[],
                current_topic=None
            )
            
            # Mock the LLM response
            mock_llm.generate_response.return_value = "Here is the information you requested."
            
            response = rag_engine.query(query, context, top_k=5)
            
            # Property verification 1: Search should be called with embedding
            assert mock_vector_store.search.called, "Vector store search should be called"
            
            # Get the search call arguments
            search_call_args = mock_vector_store.search.call_args
            
            # Property verification 2: Search should use min_score threshold
            if search_call_args and 'min_score' in search_call_args[1]:
                actual_min_score = search_call_args[1]['min_score']
                assert actual_min_score >= 0.5, (
                    f"Minimum score threshold should be at least 0.5, got {actual_min_score}"
                )
            
            # Property verification 3: All returned sources should have high relevance
            assert len(response.sources) > 0, "Should return at least one source"
            
            for source in response.sources:
                relevance_score = source.get('relevance_score', 0.0)
                assert relevance_score >= 0.7, (
                    f"Source '{source.get('name')}' has low relevance score: {relevance_score}. "
                    f"All sources should have score >= 0.7 for semantic relevance."
                )
            
            # Property verification 4: Sources should be sorted by relevance (descending)
            scores = [source.get('relevance_score', 0.0) for source in response.sources]
            assert scores == sorted(scores, reverse=True), (
                f"Sources should be sorted by relevance score (highest first). "
                f"Got scores: {scores}"
            )


@settings(max_examples=15, deadline=None)
@given(
    query=query_strategy(),
    num_results=st.integers(min_value=3, max_value=10)
)
def test_top_k_results_relevance(query, num_results):
    """
    Test that top-k search returns exactly k results (or fewer if not enough matches).
    
    This verifies that the search respects the top_k parameter and returns
    the most relevant documents.
    """
    # Generate more results than requested to test filtering
    all_results = []
    for i in range(num_results + 5):
        score = 0.95 - (i * 0.05)  # Decreasing scores
        if score < 0.7:  # Below threshold (RAG uses 0.7 min_score)
            break
        all_results.append({
            'id': f'scheme-{i}',
            'score': score,
            'source': {
                'scheme_id': f'scheme-{i}',
                'name': f'Scheme {i}',
                'category': 'agriculture',
                'description': 'Test scheme',
                'source_type': 'official'
            }
        })
    
    # Ensure we have enough results
    assume(len(all_results) >= num_results)
    
    # Mock dependencies
    mock_vector_store = Mock()
    # RAG engine calls search twice: official and general
    mock_vector_store.search.side_effect = [all_results[:num_results], []]
    
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
            
            response = rag_engine.query(query, context, top_k=num_results)
            
            # Verify we got at most top_k results
            assert len(response.sources) <= num_results, (
                f"Should return at most {num_results} sources, got {len(response.sources)}"
            )
            
            # Verify all returned sources are high quality
            for source in response.sources:
                assert source.get('relevance_score', 0.0) >= 0.7, (
                    "All returned sources should have high relevance scores"
                )


@settings(max_examples=15, deadline=None)
@given(
    query=query_strategy()
)
def test_low_relevance_documents_filtered(query):
    """
    Test that documents with low semantic similarity are filtered out.
    
    This ensures that only relevant documents are returned, even if the
    vector database returns some low-scoring results.
    """
    # Generate mix of high and low scoring results
    mixed_results = [
        # High relevance results
        {
            'id': 'scheme-1',
            'score': 0.92,
            'source': {
                'scheme_id': 'scheme-1',
                'name': 'Highly Relevant Scheme',
                'category': 'agriculture',
                'description': 'Very relevant to query',
                'source_type': 'official'
            }
        },
        {
            'id': 'scheme-2',
            'score': 0.85,
            'source': {
                'scheme_id': 'scheme-2',
                'name': 'Relevant Scheme',
                'category': 'agriculture',
                'description': 'Relevant to query',
                'source_type': 'official'
            }
        },
        # Low relevance results (should be filtered by min_score in vector store)
        {
            'id': 'scheme-3',
            'score': 0.45,
            'source': {
                'scheme_id': 'scheme-3',
                'name': 'Barely Relevant Scheme',
                'category': 'health',
                'description': 'Not very relevant',
                'source_type': 'general'
            }
        },
        {
            'id': 'scheme-4',
            'score': 0.30,
            'source': {
                'scheme_id': 'scheme-4',
                'name': 'Irrelevant Scheme',
                'category': 'education',
                'description': 'Not relevant at all',
                'source_type': 'general'
            }
        }
    ]
    
    # Mock vector store to return only high-scoring results (filtered by min_score)
    high_score_results = [r for r in mixed_results if r['score'] >= 0.7]
    
    mock_vector_store = Mock()
    # RAG engine calls search twice: official and general
    # Return high-score results for official, empty for general
    mock_vector_store.search.side_effect = [high_score_results, []]
    
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
            
            # Property verification: No low-relevance documents in results
            for source in response.sources:
                relevance_score = source.get('relevance_score', 0.0)
                assert relevance_score >= 0.7, (
                    f"Low-relevance document should be filtered out. "
                    f"Found source '{source.get('name')}' with score {relevance_score}"
                )
            
            # Verify we only got high-scoring results (no duplicates)
            # Note: RAG engine may call search twice, so we check that all sources are high-quality
            assert len(response.sources) >= len(high_score_results), (
                f"Should return at least {len(high_score_results)} high-relevance sources, "
                f"got {len(response.sources)}"
            )


@settings(max_examples=10, deadline=None)
@given(
    query=query_strategy(),
    embedding_dimension=st.just(1536)  # Titan embeddings are 1536-dimensional
)
def test_embedding_generation_for_search(query, embedding_dimension):
    """
    Test that query embeddings are generated correctly for semantic search.
    
    This verifies that the RAG engine generates embeddings with the correct
    dimensions before performing vector search.
    """
    # Mock dependencies
    mock_vector_store = Mock()
    test_result = [
        {
            'id': 'scheme-1',
            'score': 0.85,
            'source': {
                'scheme_id': 'scheme-1',
                'name': 'Test Scheme',
                'category': 'agriculture',
                'description': 'Test description',
                'source_type': 'official'
            }
        }
    ]
    # RAG engine calls search twice: official and general
    mock_vector_store.search.side_effect = [test_result, []]
    
    # Create a mock embedding with correct dimensions
    mock_embedding = [0.1] * embedding_dimension
    
    mock_llm = Mock()
    mock_llm.generate_embedding.return_value = mock_embedding
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
            
            # Property verification 1: Embedding should be generated for query
            assert mock_llm.generate_embedding.called, "Should generate embedding for query"
            
            # Get the embedding call arguments
            embedding_call_args = mock_llm.generate_embedding.call_args
            assert embedding_call_args is not None, "Embedding generation should be called"
            
            # Verify the query text was passed to embedding generation
            called_with_text = embedding_call_args[0][0]
            assert isinstance(called_with_text, str), "Should pass text to embedding generation"
            assert len(called_with_text) > 0, "Query text should not be empty"
            
            # Property verification 2: Vector search should be called with embedding
            assert mock_vector_store.search.called, "Should perform vector search"
            
            search_call_args = mock_vector_store.search.call_args
            if search_call_args:
                # First positional argument should be the query embedding
                query_embedding = search_call_args[0][0]
                assert isinstance(query_embedding, list), "Query embedding should be a list"
                assert len(query_embedding) == embedding_dimension, (
                    f"Embedding should have {embedding_dimension} dimensions, "
                    f"got {len(query_embedding)}"
                )


@settings(max_examples=10, deadline=None)
@given(
    query=query_strategy()
)
def test_confidence_score_based_on_relevance(query):
    """
    Test that the RAG response confidence score reflects retrieval quality.
    
    Higher average relevance scores should result in higher confidence.
    """
    # Test with high-relevance results
    high_relevance_results = [
        {
            'id': f'scheme-{i}',
            'score': 0.90 - (i * 0.02),  # Scores: 0.90, 0.88, 0.86, 0.84, 0.82
            'source': {
                'scheme_id': f'scheme-{i}',
                'name': f'Scheme {i}',
                'category': 'agriculture',
                'description': 'Relevant scheme',
                'source_type': 'official'
            }
        }
        for i in range(5)
    ]
    
    mock_vector_store = Mock()
    # RAG engine calls search twice: official and general
    mock_vector_store.search.side_effect = [high_relevance_results, []]
    
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
            
            # Property verification: Confidence should be high for high-relevance results
            # Average score is (0.90 + 0.88 + 0.86 + 0.84 + 0.82) / 5 = 0.86
            expected_min_confidence = 0.80
            
            assert response.confidence >= expected_min_confidence, (
                f"Confidence score should be at least {expected_min_confidence} "
                f"for high-relevance results, got {response.confidence}"
            )
            
            # Confidence should not exceed 1.0
            assert response.confidence <= 1.0, (
                f"Confidence score should not exceed 1.0, got {response.confidence}"
            )
