#!/usr/bin/env python3
"""
Basic test script for RAG engine functionality
Tests vector store, RAG engine, and conversation manager without requiring full API
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store import VectorStore, Document
from app.services.rag_engine import RAGEngine, ConversationContext
from app.services.conversation_manager import ConversationManager


def test_vector_store():
    """Test vector store basic functionality"""
    print("\n=== Testing Vector Store ===")
    
    try:
        # Create vector store
        vs = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_faiss_index"
        )
        print("✓ Vector store initialized")
        
        # Create test documents
        docs = [
            Document(
                doc_id="doc1",
                content="The PM-KISAN scheme provides ₹6000 per year to farmers in three installments.",
                metadata={"category": "agriculture"},
                source="Ministry of Agriculture",
                source_type="official",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Document(
                doc_id="doc2",
                content="Ayushman Bharat provides health insurance coverage up to ₹5 lakh per family per year.",
                metadata={"category": "health"},
                source="National Health Authority",
                source_type="official",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Document(
                doc_id="doc3",
                content="Pradhan Mantri Mudra Yojana offers loans up to ₹10 lakh for small businesses.",
                metadata={"category": "employment"},
                source="Ministry of Finance",
                source_type="official",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Add documents
        vs.add_documents(docs)
        print(f"✓ Added {len(docs)} documents")
        
        # Test search
        results = vs.search("farmer benefits", top_k=2)
        print(f"✓ Search returned {len(results)} results")
        
        if results:
            print(f"  Top result: {results[0].document.content[:80]}...")
            print(f"  Score: {results[0].score:.3f}")
        
        # Get stats
        stats = vs.get_stats()
        print(f"✓ Vector store stats: {stats['total_documents']} documents")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_engine():
    """Test RAG engine basic functionality"""
    print("\n=== Testing RAG Engine ===")
    
    try:
        # Create vector store with test data
        vs = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_faiss_index"
        )
        
        # Add test documents if empty
        if vs.get_stats()['total_documents'] == 0:
            docs = [
                Document(
                    doc_id="doc1",
                    content="The PM-KISAN scheme provides ₹6000 per year to farmers.",
                    metadata={"category": "agriculture"},
                    source="Ministry of Agriculture",
                    source_type="official",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            vs.add_documents(docs)
        
        # Create RAG engine (without LLM for basic test)
        rag = RAGEngine(
            vector_store=vs,
            llm_provider="mock",  # Use mock provider for testing
            llm_model="test"
        )
        print("✓ RAG engine initialized")
        
        # Test query (will use fallback response without real LLM)
        response = rag.query(
            user_query="What benefits are available for farmers?",
            top_k=3
        )
        print(f"✓ Query processed")
        print(f"  Sources found: {len(response.sources)}")
        print(f"  Confidence: {response.confidence:.3f}")
        print(f"  Answer preview: {response.answer[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ RAG engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_manager():
    """Test conversation manager basic functionality"""
    print("\n=== Testing Conversation Manager ===")
    
    try:
        # Note: This requires Redis to be running
        # We'll catch the error if Redis is not available
        
        conv_manager = ConversationManager(session_ttl_hours=1)
        print("✓ Conversation manager initialized")
        
        # Create session
        session_id = conv_manager.create_session(
            user_id="test_user",
            language="en"
        )
        print(f"✓ Created session: {session_id}")
        
        # Get context
        context = conv_manager.get_context(session_id)
        if context:
            print(f"✓ Retrieved context for session")
            print(f"  User ID: {context.user_id}")
            print(f"  Language: {context.language}")
        
        # Add turn
        success = conv_manager.add_turn(
            session_id=session_id,
            user_message="What is PM-KISAN?",
            assistant_message="PM-KISAN is a scheme that provides financial support to farmers."
        )
        print(f"✓ Added conversation turn: {success}")
        
        # Get stats
        stats = conv_manager.get_session_stats(session_id)
        if stats:
            print(f"✓ Session stats: {stats['num_turns']} turns")
        
        # Clean up
        conv_manager.delete_session(session_id)
        print(f"✓ Deleted session")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversation manager test failed: {e}")
        print("  Note: This test requires Redis to be running")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("RAG Engine Basic Functionality Tests")
    print("=" * 60)
    
    results = []
    
    # Test vector store
    results.append(("Vector Store", test_vector_store()))
    
    # Test RAG engine
    results.append(("RAG Engine", test_rag_engine()))
    
    # Test conversation manager
    results.append(("Conversation Manager", test_conversation_manager()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    return all(passed for _, passed in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
