# RAG Engine Implementation Documentation

## Overview

The RAG (Retrieval-Augmented Generation) engine is a core component of BharatSahayak that combines semantic search with Large Language Models (LLMs) to provide contextual, accurate responses to user queries.

## Architecture

### Components

1. **Vector Store** (`app/services/vector_store.py`)
   - FAISS-based vector database for document storage and retrieval
   - Sentence-transformers for multilingual embeddings
   - Supports semantic search with similarity scoring
   - Prioritizes official sources in search results

2. **RAG Engine** (`app/services/rag_engine.py`)
   - Query processing pipeline
   - Context retrieval from vector store
   - LLM integration for response generation
   - Confidence scoring based on retrieval quality

3. **Conversation Manager** (`app/services/conversation_manager.py`)
   - Session management using Redis
   - Conversation context storage
   - Multi-turn conversation support
   - Automatic session expiration (24 hours default)

4. **API Endpoints** (`app/api/rag.py`)
   - POST /api/ask - Submit queries and receive AI responses
   - POST /api/session/create - Create conversation sessions
   - DELETE /api/session/{session_id} - Clear session history
   - GET /api/session/{session_id}/stats - Get session statistics
   - POST /api/documents/add - Add documents to knowledge base
   - GET /api/documents/stats - Get vector store statistics

## Installation

### Dependencies

Add to `requirements.txt`:
```
sentence-transformers==2.3.1
faiss-cpu==1.7.4
langchain==0.1.0
langchain-community==0.0.13
openai==1.7.2
```

Install:
```bash
pip install -r requirements.txt
```

### Configuration

Add to `.env`:
```
OPENAI_API_KEY=your-openai-api-key-here
```

## Usage

### 1. Initialize Vector Store

```python
from app.services.vector_store import VectorStore, Document
from datetime import datetime

# Create vector store
vs = VectorStore(
    embedding_model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    index_path="data/faiss_index"
)

# Add documents
documents = [
    Document(
        doc_id="scheme_001",
        content="PM-KISAN provides ₹6000 per year to farmers in three installments.",
        metadata={"category": "agriculture", "scheme_id": "PM-KISAN"},
        source="Ministry of Agriculture",
        source_type="official",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
]

vs.add_documents(documents)
vs.save_index()
```

### 2. Query with RAG Engine

```python
from app.services.rag_engine import RAGEngine

# Initialize RAG engine
rag = RAGEngine(
    vector_store=vs,
    llm_provider="openai",
    llm_model="gpt-3.5-turbo"
)

# Process query
response = rag.query(
    user_query="What benefits are available for farmers?",
    top_k=5,
    min_score=0.7
)

print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
print(f"Sources: {len(response.sources)}")
```

### 3. Manage Conversations

```python
from app.services.conversation_manager import ConversationManager

# Initialize manager
conv_manager = ConversationManager(session_ttl_hours=24)

# Create session
session_id = conv_manager.create_session(
    user_id="user_123",
    language="en"
)

# Get context
context = conv_manager.get_context(session_id)

# Query with context
response = rag.query(
    user_query="Tell me more about the eligibility",
    context=context
)

# Add turn to history
conv_manager.add_turn(
    session_id=session_id,
    user_message="Tell me more about the eligibility",
    assistant_message=response.answer
)
```

### 4. API Usage

#### Ask a Question

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is PM-KISAN scheme?",
    "language": "en",
    "top_k": 5,
    "min_score": 0.7
  }'
```

#### Create Session

```bash
curl -X POST "http://localhost:8000/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "language": "en"
  }'
```

#### Query with Session Context

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the eligibility criteria?",
    "session_id": "session-uuid-here",
    "language": "en"
  }'
```

## Features

### Semantic Search

- Uses multilingual sentence embeddings for cross-language search
- Cosine similarity scoring for relevance ranking
- Configurable minimum score threshold
- Source type filtering (official, verified, general)

### Source Prioritization

The system automatically prioritizes official sources:
1. Official government sources ranked highest
2. Verified sources ranked second
3. General sources ranked last

### Conversation Context

- Maintains conversation history across multiple turns
- Includes last 3 turns in LLM prompt for context
- Automatic session expiration after 24 hours
- Redis-based storage for scalability

### Confidence Scoring

Confidence is calculated based on:
- Top result similarity score (60% weight)
- Number of relevant results found (20% weight)
- Presence of official sources (20% weight)

### Multilingual Support

- Supports Hindi, English, and other Indian languages
- Uses multilingual embedding model
- Language-specific response generation

## Data Models

### Document

```python
@dataclass
class Document:
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    source_type: str  # 'official', 'verified', 'general'
    created_at: datetime
    updated_at: datetime
```

### SearchResult

```python
@dataclass
class SearchResult:
    document: Document
    score: float
    rank: int
```

### RAGResponse

```python
@dataclass
class RAGResponse:
    answer: str
    sources: List[SearchResult]
    confidence: float
    context_used: bool
    language: str
    metadata: Optional[Dict[str, Any]]
```

### ConversationContext

```python
@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    language: str
    history: List[ConversationTurn]
    user_profile: Optional[Dict[str, Any]]
    current_topic: Optional[str]
    created_at: datetime
    last_activity: datetime
```

## Testing

### Basic Functionality Test

```bash
python scripts/test_rag_basic.py
```

This tests:
- Vector store initialization and document addition
- Semantic search functionality
- RAG query processing
- Conversation manager operations

### Requirements

- Redis must be running for conversation manager tests
- OpenAI API key required for full LLM integration tests

## Performance Considerations

### Vector Store

- FAISS IndexFlatIP provides exact search with cosine similarity
- For large datasets (>1M documents), consider IndexIVFFlat for faster search
- Embeddings are normalized for efficient cosine similarity computation

### Caching

- Redis stores conversation context with TTL
- Vector store index can be saved/loaded from disk
- Consider caching frequent queries

### Scalability

- Vector store supports batch embedding for efficiency
- Conversation manager uses Redis for distributed sessions
- API endpoints support concurrent requests

## Error Handling

### Vector Store Errors

- Missing dependencies: Install faiss-cpu and sentence-transformers
- Index not found: Automatically creates new index
- Embedding failures: Returns empty results

### RAG Engine Errors

- LLM API failures: Returns fallback error message
- No relevant documents: Returns out-of-scope response
- Context retrieval errors: Proceeds without context

### Conversation Manager Errors

- Redis connection failures: Logged and returns None
- Session not found: Returns 404 error
- Serialization errors: Logged and returns error

## Future Enhancements

1. **Advanced Retrieval**
   - Hybrid search (semantic + keyword)
   - Re-ranking with cross-encoders
   - Query expansion and reformulation

2. **LLM Integration**
   - Support for local models (LLaMA, Mistral)
   - Fine-tuned models for Indian context
   - Streaming responses

3. **Multilingual Improvements**
   - Language-specific embedding models
   - Translation integration
   - Code-mixed query handling

4. **Analytics**
   - Query performance tracking
   - Source usage statistics
   - User satisfaction metrics

## References

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain](https://python.langchain.com/)
- [OpenAI API](https://platform.openai.com/docs)
