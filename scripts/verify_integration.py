"""
Verify integration of all BharatSahayak components
Tests that all components can be imported and initialized
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all integration components can be imported"""
    print("Testing component imports...")
    
    try:
        # Voice Interface
        from app.services.voice_interface import get_stt_engine, get_tts_engine
        print("✓ Voice Interface imports successful")
        
        # RAG Engine
        from app.services.rag_engine import RAGEngine, ConversationContext
        from app.services.vector_store import VectorStore
        from app.services.conversation_manager import ConversationManager
        print("✓ RAG Engine imports successful")
        
        # Domain Services
        from app.services.scheme_repository import SchemeRepository
        from app.services.crop_advisor import CropAdvisor
        from app.services.skills_matcher import SkillsMatcher
        from app.services.health_advisor import HealthAdvisor
        print("✓ Domain Services imports successful")
        
        # Impact Tracker
        from app.services.impact_tracker import ImpactTracker
        from app.schemas.impact import InteractionEventCreate, OutcomeEventCreate
        print("✓ Impact Tracker imports successful")
        
        # Integration Orchestrator
        from app.services.integration_orchestrator import IntegrationOrchestrator
        print("✓ Integration Orchestrator imports successful")
        
        # API Endpoints
        from app.api.voice import router as voice_router
        from app.api.rag import router as rag_router
        from app.api.schemes import router as schemes_router
        from app.api.farmer import router as farmer_router
        from app.api.skills import router as skills_router
        from app.api.health_advisory import router as health_router
        from app.api.impact import router as impact_router
        from app.api.integrated import router as integrated_router
        print("✓ API Endpoints imports successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {str(e)}")
        return False


def test_orchestrator_initialization():
    """Test that orchestrator can be initialized"""
    print("\nTesting orchestrator initialization...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        from app.services.vector_store import VectorStore
        from app.services.rag_engine import RAGEngine
        from app.services.conversation_manager import ConversationManager
        from app.services.integration_orchestrator import IntegrationOrchestrator
        
        # Create test database
        engine = create_engine("sqlite:///./test_verify.db")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialize components
        vector_store = VectorStore(
            embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            index_path="data/test_faiss_index"
        )
        print("  ✓ Vector Store initialized")
        
        rag_engine = RAGEngine(
            vector_store=vector_store,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        print("  ✓ RAG Engine initialized")
        
        conversation_manager = ConversationManager(session_ttl_hours=24)
        print("  ✓ Conversation Manager initialized")
        
        orchestrator = IntegrationOrchestrator(
            db=db,
            vector_store=vector_store,
            rag_engine=rag_engine,
            conversation_manager=conversation_manager
        )
        print("  ✓ Integration Orchestrator initialized")
        
        db.close()
        
        # Cleanup
        import os
        if os.path.exists("test_verify.db"):
            os.remove("test_verify.db")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_registration():
    """Test that all API routers are registered"""
    print("\nTesting API router registration...")
    
    try:
        from app.main import app
        
        # Get all registered routes
        routes = [route.path for route in app.routes]
        
        # Check for key endpoints
        required_endpoints = [
            "/health",
            "/api/voice-to-text",
            "/api/ask",
            "/api/schemes",
            "/api/farmer/crop-advice",
            "/api/skills",
            "/api/health/check",
            "/api/impact/event",
            "/api/integrated/voice-query"
        ]
        
        missing = []
        for endpoint in required_endpoints:
            if endpoint not in routes:
                missing.append(endpoint)
        
        if missing:
            print(f"  ✗ Missing endpoints: {missing}")
            return False
        
        print(f"  ✓ All {len(required_endpoints)} required endpoints registered")
        return True
        
    except Exception as e:
        print(f"  ✗ API registration check failed: {str(e)}")
        return False


def test_integration_flows():
    """Test that integration flows are defined"""
    print("\nTesting integration flow definitions...")
    
    try:
        from app.services.integration_orchestrator import IntegrationOrchestrator
        
        # Check that orchestrator has required methods
        required_methods = [
            'process_voice_query',
            'track_scheme_access',
            'track_scheme_application',
            'track_crop_advice',
            'track_job_discovery',
            'track_health_check'
        ]
        
        missing = []
        for method in required_methods:
            if not hasattr(IntegrationOrchestrator, method):
                missing.append(method)
        
        if missing:
            print(f"  ✗ Missing methods: {missing}")
            return False
        
        print(f"  ✓ All {len(required_methods)} integration methods defined")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration flow check failed: {str(e)}")
        return False


def main():
    """Run all verification tests"""
    print("="*80)
    print("BharatSahayak Integration Verification")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Component Imports", test_imports()))
    results.append(("Orchestrator Initialization", test_orchestrator_initialization()))
    results.append(("API Registration", test_api_registration()))
    results.append(("Integration Flows", test_integration_flows()))
    
    # Summary
    print("\n" + "="*80)
    print("Verification Summary")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All integration components verified successfully!")
        print("✓ System is fully integrated and ready for end-to-end testing")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("✗ Please fix the issues before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
