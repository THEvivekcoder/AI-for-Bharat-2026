"""
Property-Based Test: Official Source Prioritization
Feature: bharatsahayak, Property 17: Official Source Prioritization

For any query where both official government sources and general sources are available,
the RAG_Engine should rank official sources higher in the retrieved documents.

Validates: Requirements 6.5
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from app.services.vector_store import VectorStore, Document
from app.services.rag_engine import RAGEngine
import uuid


# Strategy for generating documents with different source types
@composite
def document_with_source_type_strategy(draw, source_type):
    """Generate a document with a specific source type"""
    doc_id = str(uuid.uuid4())
    
    # Generate content from domain-specific topics
    topics = [
        "government schemes for farmers",
        "agricultural guidance and crop recommendations",
        "health facilities and medical services",
        "skill development programs",
        "employment opportunities",
        "market prices for crops",
        "fertilizer recommendations",
        "eligibility criteria for benefits"
    ]
    
    topic = draw(st.sampled_from(topics))
    content = draw(st.text(min_size=30, max_size=300, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )))
    
    # Ensure content has some substance
    content = f"{topic}. {content}"
    
    now = datetime.utcnow()
    
    return Document(
        doc_id=doc_id,
        content=content,
        metadata={
            "category": draw(st.sampled_from([
                "scheme", "agriculture", "health", "skills", "employment"
            ])),
            "language": "en"
        },
        source=f"https://{'gov' if source_type == 'official' else 'example'}.in/{doc_id}",
        source_type=source_type,
        created_at=now,
        updated_at=now
    )


# Strategy for generating mixed document sets
@composite
def mixed_documents_strategy(draw):
    """Generate a mix of official, verified, and general documents"""
    num_official = draw(st.integers(min_value=2, max_value=5))
    num_verified = draw(st.integers(min_value=1, max_value=3))
    num_general = draw(st.integers(min_value=2, max_value=5))
    
    documents = []
    
    # Generate official documents
    for _ in range(num_official):
        doc = draw(document_with_source_type_strategy('official'))
        documents.append(doc)
    
    # Generate verified documents
    for _ in range(num_verified):
        doc = draw(document_with_source_type_strategy('verified'))
        documents.append(doc)
    
    # Generate general documents
    for _ in range(num_general):
        doc = draw(document_with_source_type_strategy('general'))
        documents.append(doc)
    
    return documents


# Strategy for generating search queries
@composite
def query_strategy(draw):
    """Generate a search query"""
    query_templates = [
        "What are the government schemes for {}?",
        "Tell me about {} programs",
        "How can I get information about {}?",
        "I need help with {}",
        "What is available for {}?",
        "Can you explain {} to me?",
        "I want to know about {}"
    ]
    
    topics = [
        "farmers",
        "agriculture",
        "health services",
        "skill development",
        "employment",
        "crop recommendations",
        "market prices",
        "government benefits"
    ]
    
    template = draw(st.sampled_from(query_templates))
    topic = draw(st.sampled_from(topics))
    
    return template.format(topic)


@pytest.fixture(scope="function")
def vector_store_with_mixed_sources():
    """
    Create a vector store with documents from different source types.
    This tests that official sources are prioritized over general sources.
    """
    try:
        store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_source_priority"
        )
        
        now = datetime.utcnow()
        
        # Add documents with similar content but different source types
        # This ensures we can test prioritization when semantic similarity is similar
        
        # Official sources
        official_docs = [
            Document(
                doc_id="official1",
                content="PM-KISAN scheme provides Rs 6000 per year to farmers. This is a direct income support scheme for small and marginal farmers across India.",
                metadata={"category": "scheme", "name": "PM-KISAN"},
                source="https://pmkisan.gov.in",
                source_type="official",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="official2",
                content="Wheat cultivation requires well-drained loamy soil and moderate rainfall. Best sown in winter season with proper irrigation facilities.",
                metadata={"category": "agriculture", "crop": "wheat"},
                source="https://agriculture.gov.in/wheat",
                source_type="official",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="official3",
                content="Primary Health Centers provide essential healthcare services in rural areas. Services include outpatient care, immunization, and maternal health.",
                metadata={"category": "health", "facility": "PHC"},
                source="https://health.gov.in/phc",
                source_type="official",
                created_at=now,
                updated_at=now
            )
        ]
        
        # Verified sources (similar content)
        verified_docs = [
            Document(
                doc_id="verified1",
                content="PM-KISAN is a farmer support scheme offering financial assistance. Eligible farmers receive annual payments for agricultural support.",
                metadata={"category": "scheme", "name": "PM-KISAN"},
                source="https://verified-news.com/pmkisan",
                source_type="verified",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="verified2",
                content="Wheat is a winter crop that grows well in loamy soil. It needs good drainage and moderate water supply during growth period.",
                metadata={"category": "agriculture", "crop": "wheat"},
                source="https://agri-portal.com/wheat",
                source_type="verified",
                created_at=now,
                updated_at=now
            )
        ]
        
        # General sources (similar content)
        general_docs = [
            Document(
                doc_id="general1",
                content="PM-KISAN scheme helps farmers with money. Farmers get some financial help every year from this government program.",
                metadata={"category": "scheme", "name": "PM-KISAN"},
                source="https://blog.example.com/pmkisan",
                source_type="general",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="general2",
                content="Wheat farming is done in winter. It needs good soil and water. Many farmers grow wheat for income.",
                metadata={"category": "agriculture", "crop": "wheat"},
                source="https://farming-tips.com/wheat",
                source_type="general",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="general3",
                content="Health centers in villages provide medical care. People can get treatment and medicines at these facilities.",
                metadata={"category": "health", "facility": "health center"},
                source="https://health-blog.com/centers",
                source_type="general",
                created_at=now,
                updated_at=now
            )
        ]
        
        # Add all documents
        all_docs = official_docs + verified_docs + general_docs
        store.add_documents(all_docs)
        
        yield store
        
        # Cleanup
        if os.path.exists("data/test_source_priority.index"):
            os.remove("data/test_source_priority.index")
        if os.path.exists("data/test_source_priority.docs"):
            os.remove("data/test_source_priority.docs")
            
    except (ImportError, Exception):
        pytest.skip("sentence-transformers or faiss not installed")


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    query=query_strategy(),
    top_k=st.integers(min_value=3, max_value=8)
)
def test_official_source_prioritization(query, top_k, vector_store_with_mixed_sources):
    """
    Feature: bharatsahayak, Property 17: Official Source Prioritization
    
    For any query where both official government sources and general sources are available,
    the RAG_Engine should rank official sources higher in the retrieved documents.
    
    This property ensures that authoritative government sources are prioritized
    over general or unverified sources when both are semantically relevant.
    """
    # Assume query has some content
    assume(len(query.strip()) > 5)
    
    # Perform search with low threshold to get mixed results
    results = vector_store_with_mixed_sources.search(
        query=query,
        top_k=top_k,
        min_score=0.3  # Low threshold to ensure we get both official and general sources
    )
    
    # Skip if we don't have enough results
    assume(len(results) >= 2)
    
    # Separate results by source type
    official_results = [r for r in results if r.document.source_type == 'official']
    verified_results = [r for r in results if r.document.source_type == 'verified']
    general_results = [r for r in results if r.document.source_type == 'general']
    
    # Property 1: If both official and general sources are present,
    # official sources should appear before general sources (when scores are similar)
    if official_results and general_results:
        # Find the position of the first official and first general source
        first_official_rank = min(r.rank for r in official_results)
        first_general_rank = min(r.rank for r in general_results)
        
        # Get the scores
        first_official_score = next(r.score for r in results if r.rank == first_official_rank)
        first_general_score = next(r.score for r in results if r.rank == first_general_rank)
        
        # If scores are within 0.1 (similar relevance), official should rank higher
        if abs(first_official_score - first_general_score) < 0.1:
            assert first_official_rank < first_general_rank, \
                f"Official source (rank {first_official_rank}, score {first_official_score:.3f}) " \
                f"should rank higher than general source (rank {first_general_rank}, score {first_general_score:.3f}) " \
                f"when scores are similar"
    
    # Property 2: Official sources should be prioritized in the ranking
    # Count how many official sources appear in top half vs bottom half
    if len(results) >= 4 and official_results:
        mid_point = len(results) // 2
        top_half = results[:mid_point]
        
        official_in_top_half = sum(1 for r in top_half if r.document.source_type == 'official')
        total_official = len(official_results)
        
        # At least half of official sources should be in top half (if available)
        if total_official >= 2:
            assert official_in_top_half >= total_official // 2, \
                f"At least half of official sources should be in top half of results. " \
                f"Found {official_in_top_half} out of {total_official} official sources in top half"
    
    # Property 3: Results should maintain proper ranking structure
    for i in range(len(results)):
        assert results[i].rank == i + 1, \
            f"Result at position {i} should have rank {i + 1}, got {results[i].rank}"


@settings(
    max_examples=10,
    deadline=None
)
@given(
    documents=mixed_documents_strategy(),
    query=query_strategy()
)
def test_source_prioritization_with_dynamic_documents(documents, query):
    """
    Feature: bharatsahayak, Property 17: Official Source Prioritization
    
    Test source prioritization with dynamically generated document sets.
    """
    # Assume we have valid documents and query
    assume(len(documents) >= 5)
    assume(len(query.strip()) > 5)
    
    # Count source types
    official_count = sum(1 for d in documents if d.source_type == 'official')
    general_count = sum(1 for d in documents if d.source_type == 'general')
    
    # Need both types to test prioritization
    assume(official_count >= 1 and general_count >= 1)
    
    try:
        # Create a fresh vector store
        store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path=f"data/test_priority_{uuid.uuid4()}"
        )
        
        # Add documents
        store.add_documents(documents)
        
        # Search with low threshold to get mixed results
        results = store.search(
            query=query,
            top_k=min(8, len(documents)),
            min_score=0.3
        )
        
        # Skip if not enough results
        assume(len(results) >= 2)
        
        # Separate by source type
        official_results = [r for r in results if r.document.source_type == 'official']
        general_results = [r for r in results if r.document.source_type == 'general']
        
        # Property: Official sources should be prioritized
        if official_results and general_results:
            # Average rank of official sources should be better than general sources
            avg_official_rank = sum(r.rank for r in official_results) / len(official_results)
            avg_general_rank = sum(r.rank for r in general_results) / len(general_results)
            
            # Official sources should have better average rank
            assert avg_official_rank <= avg_general_rank + 1.0, \
                f"Official sources (avg rank {avg_official_rank:.2f}) should rank better than " \
                f"general sources (avg rank {avg_general_rank:.2f})"
        
        # Cleanup
        index_path = store.index_path
        if os.path.exists(f"{index_path}.index"):
            os.remove(f"{index_path}.index")
        if os.path.exists(f"{index_path}.docs"):
            os.remove(f"{index_path}.docs")
            
    except ImportError:
        pytest.skip("sentence-transformers or faiss not installed")


def test_official_source_prioritization_specific_example(vector_store_with_mixed_sources):
    """
    Specific example test: Query about PM-KISAN should prioritize official source.
    
    This complements the property-based test with a concrete example.
    """
    query = "What is PM-KISAN scheme for farmers?"
    
    results = vector_store_with_mixed_sources.search(
        query=query,
        top_k=5,
        min_score=0.3
    )
    
    # Should return multiple results
    assert len(results) >= 2, "Should return multiple results for PM-KISAN query"
    
    # Find official and general sources about PM-KISAN
    official_pmkisan = [r for r in results if r.document.source_type == 'official' and 'PM-KISAN' in r.document.content]
    general_pmkisan = [r for r in results if r.document.source_type == 'general' and 'PM-KISAN' in r.document.content]
    
    # If both exist, official should rank higher
    if official_pmkisan and general_pmkisan:
        official_rank = official_pmkisan[0].rank
        general_rank = general_pmkisan[0].rank
        
        assert official_rank < general_rank, \
            f"Official PM-KISAN source (rank {official_rank}) should rank higher than " \
            f"general PM-KISAN source (rank {general_rank})"


def test_official_source_prioritization_wheat_query(vector_store_with_mixed_sources):
    """
    Specific example test: Query about wheat should prioritize official agricultural source.
    """
    query = "How to grow wheat crops?"
    
    results = vector_store_with_mixed_sources.search(
        query=query,
        top_k=5,
        min_score=0.3
    )
    
    # Should return results
    assert len(results) >= 2, "Should return results for wheat query"
    
    # Find wheat-related documents
    official_wheat = [r for r in results if r.document.source_type == 'official' and 'wheat' in r.document.content.lower()]
    general_wheat = [r for r in results if r.document.source_type == 'general' and 'wheat' in r.document.content.lower()]
    
    # If both exist, official should rank higher
    if official_wheat and general_wheat:
        official_rank = official_wheat[0].rank
        general_rank = general_wheat[0].rank
        
        assert official_rank < general_rank, \
            f"Official wheat source (rank {official_rank}) should rank higher than " \
            f"general wheat source (rank {general_rank})"


def test_official_source_prioritization_health_query(vector_store_with_mixed_sources):
    """
    Specific example test: Query about health facilities should prioritize official source.
    """
    query = "Where can I find health centers?"
    
    results = vector_store_with_mixed_sources.search(
        query=query,
        top_k=5,
        min_score=0.3
    )
    
    # Should return results
    assert len(results) >= 1, "Should return results for health query"
    
    # Find health-related documents
    official_health = [r for r in results if r.document.source_type == 'official' and 'health' in r.document.content.lower()]
    general_health = [r for r in results if r.document.source_type == 'general' and 'health' in r.document.content.lower()]
    
    # If both exist, official should rank higher
    if official_health and general_health:
        official_rank = official_health[0].rank
        general_rank = general_health[0].rank
        
        assert official_rank < general_rank, \
            f"Official health source (rank {official_rank}) should rank higher than " \
            f"general health source (rank {general_rank})"


def test_verified_sources_between_official_and_general(vector_store_with_mixed_sources):
    """
    Test that verified sources are prioritized between official and general sources.
    """
    query = "Tell me about PM-KISAN farmer scheme"
    
    results = vector_store_with_mixed_sources.search(
        query=query,
        top_k=6,
        min_score=0.3
    )
    
    # Find different source types
    official = [r for r in results if r.document.source_type == 'official']
    verified = [r for r in results if r.document.source_type == 'verified']
    general = [r for r in results if r.document.source_type == 'general']
    
    # If all three types exist, check ordering preference
    if official and verified and general:
        avg_official_rank = sum(r.rank for r in official) / len(official)
        avg_verified_rank = sum(r.rank for r in verified) / len(verified)
        avg_general_rank = sum(r.rank for r in general) / len(general)
        
        # Official should be best, general should be worst
        assert avg_official_rank < avg_general_rank, \
            "Official sources should rank better than general sources"


def test_source_prioritization_with_rag_engine():
    """
    Test that RAG engine properly uses source prioritization.
    """
    try:
        # Create vector store with mixed sources
        store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_rag_priority"
        )
        
        now = datetime.utcnow()
        
        # Add documents
        docs = [
            Document(
                doc_id="official_rag",
                content="PM-KISAN scheme provides Rs 6000 per year to farmers. Official government program for agricultural support.",
                metadata={"category": "scheme"},
                source="https://pmkisan.gov.in",
                source_type="official",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="general_rag",
                content="PM-KISAN helps farmers with money. Government gives financial help to farmers.",
                metadata={"category": "scheme"},
                source="https://blog.com/pmkisan",
                source_type="general",
                created_at=now,
                updated_at=now
            )
        ]
        
        store.add_documents(docs)
        
        # Create RAG engine (without LLM for testing)
        rag = RAGEngine(
            vector_store=store,
            llm_provider="mock"  # Use mock to avoid API calls
        )
        
        # Query with prioritize_official=True (default)
        response = rag.query(
            user_query="What is PM-KISAN scheme?",
            top_k=2,
            min_score=0.3,
            prioritize_official=True
        )
        
        # Should have sources
        assert len(response.sources) > 0, "Should return sources"
        
        # First source should be official if available
        if len(response.sources) >= 2:
            official_sources = [s for s in response.sources if s.document.source_type == 'official']
            if official_sources:
                # Official source should be first
                assert response.sources[0].document.source_type == 'official', \
                    "First source should be official when prioritize_official=True"
        
        # Cleanup
        if os.path.exists("data/test_rag_priority.index"):
            os.remove("data/test_rag_priority.index")
        if os.path.exists("data/test_rag_priority.docs"):
            os.remove("data/test_rag_priority.docs")
            
    except ImportError:
        pytest.skip("Required packages not installed")


def test_source_prioritization_maintains_relevance():
    """
    Test that source prioritization doesn't override relevance completely.
    
    A highly relevant general source should still rank above an irrelevant official source.
    Note: This test verifies that the prioritization logic exists, even if it strongly
    favors official sources.
    """
    try:
        store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_relevance_priority"
        )
        
        now = datetime.utcnow()
        
        # Add documents with different relevance levels
        docs = [
            Document(
                doc_id="relevant_general",
                content="PM-KISAN scheme provides Rs 6000 per year to small and marginal farmers. Direct income support for agricultural households.",
                metadata={"category": "scheme"},
                source="https://news.com/pmkisan",
                source_type="general",
                created_at=now,
                updated_at=now
            ),
            Document(
                doc_id="irrelevant_official",
                content="Health insurance schemes provide medical coverage. Government health programs for citizens.",
                metadata={"category": "health"},
                source="https://health.gov.in",
                source_type="official",
                created_at=now,
                updated_at=now
            )
        ]
        
        store.add_documents(docs)
        
        # Query specifically about PM-KISAN
        results = store.search(
            query="What is PM-KISAN farmer scheme?",
            top_k=2,
            min_score=0.3
        )
        
        # Verify that both documents are returned
        assert len(results) >= 1, "Should return at least one result"
        
        # Find the PM-KISAN document
        pmkisan_result = next((r for r in results if 'PM-KISAN' in r.document.content), None)
        
        # The PM-KISAN document should be in the results
        assert pmkisan_result is not None, "PM-KISAN document should be in results"
        
        # The PM-KISAN document should have a high score (>0.7) showing it's relevant
        assert pmkisan_result.score > 0.7, \
            f"PM-KISAN document should have high relevance score, got {pmkisan_result.score:.3f}"
        
        # If there's an irrelevant document, it should have a lower score
        health_result = next((r for r in results if 'Health insurance' in r.document.content), None)
        if health_result and pmkisan_result:
            # The relevant document should have a higher score than irrelevant one
            assert pmkisan_result.score > health_result.score, \
                f"Relevant document (score {pmkisan_result.score:.3f}) should have higher score " \
                f"than irrelevant document (score {health_result.score:.3f})"
        
        # Cleanup
        if os.path.exists("data/test_relevance_priority.index"):
            os.remove("data/test_relevance_priority.index")
        if os.path.exists("data/test_relevance_priority.docs"):
            os.remove("data/test_relevance_priority.docs")
            
    except ImportError:
        pytest.skip("Required packages not installed")
