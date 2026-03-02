"""
RAG Engine Service

Provides Retrieval-Augmented Generation capabilities using:
- Amazon OpenSearch for vector storage and semantic search
- Amazon Bedrock for LLM inference and embeddings
- Conversation context management
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    user_message: str
    assistant_message: str
    timestamp: datetime
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Manages conversation state and history"""
    session_id: str
    user_id: str
    language: str
    history: List[ConversationTurn] = field(default_factory=list)
    current_topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RAGResponse:
    """Response from RAG query"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    session_id: str


class OpenSearchVectorStore:
    """Manages vector storage and retrieval using OpenSearch"""
    
    def __init__(self, endpoint: str, index_name: str = "schemes"):
        """
        Initialize OpenSearch client
        
        Args:
            endpoint: OpenSearch domain endpoint
            index_name: Name of the index to use
        """
        self.endpoint = endpoint
        self.index_name = index_name
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Set up AWS authentication
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            'es',
            session_token=credentials.token
        )
        
        # Create OpenSearch client
        self.client = OpenSearch(
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
    
    def create_index(self) -> bool:
        """
        Create OpenSearch index with vector field mapping
        
        Returns:
            True if index created successfully
        """
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512
                }
            },
            "mappings": {
                "properties": {
                    "scheme_id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "category": {"type": "keyword"},
                    "description": {"type": "text"},
                    "benefits": {"type": "text"},
                    "eligibility_criteria": {"type": "object"},
                    "content_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,  # Titan embeddings dimension
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    "source_type": {"type": "keyword"},  # official, general
                    "last_updated": {"type": "date"}
                }
            }
        }
        
        try:
            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(index=self.index_name, body=index_body)
                return True
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    def index_document(self, doc_id: str, content: str, embedding: List[float], 
                      metadata: Dict[str, Any]) -> bool:
        """
        Index a document with its vector embedding
        
        Args:
            doc_id: Unique document identifier
            content: Text content
            embedding: Vector embedding
            metadata: Additional metadata (scheme_id, category, etc.)
            
        Returns:
            True if indexed successfully
        """
        document = {
            "content": content,
            "content_vector": embedding,
            **metadata,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document,
                refresh=True
            )
            return True
        except Exception as e:
            print(f"Error indexing document {doc_id}: {e}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5, 
               filters: Optional[Dict[str, Any]] = None,
               min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filters: Optional filters (category, source_type, etc.)
            min_score: Minimum similarity score threshold
            
        Returns:
            List of matching documents with scores
        """
        # Build KNN query
        knn_query = {
            "size": top_k,
            "query": {
                "knn": {
                    "content_vector": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": {
                "excludes": ["content_vector"]  # Don't return the vector
            }
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})
            
            knn_query["query"] = {
                "bool": {
                    "must": [knn_query["query"]],
                    "filter": filter_clauses
                }
            }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=knn_query
            )
            
            results = []
            for hit in response['hits']['hits']:
                score = hit['_score']
                if score >= min_score:
                    results.append({
                        'id': hit['_id'],
                        'score': score,
                        'source': hit['_source']
                    })
            
            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return []


class BedrockLLMService:
    """Service for interacting with Amazon Bedrock LLMs"""
    
    def __init__(self, model_id: str = "anthropic.claude-instant-v1", 
                 embedding_model_id: str = "amazon.titan-embed-text-v1"):
        """
        Initialize Bedrock client
        
        Args:
            model_id: Bedrock model ID for text generation
            embedding_model_id: Bedrock model ID for embeddings
        """
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.model_id = model_id
        self.embedding_model_id = embedding_model_id
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Titan
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        body = json.dumps({
            "inputText": text
        })
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def generate_response(self, prompt: str, max_tokens: int = 500, 
                         temperature: float = 0.7) -> str:
        """
        Generate text response using Claude
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        # Format for Claude
        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "stop_sequences": ["\n\nHuman:"]
        })
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['completion'].strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine
    
    Combines vector search with LLM generation for contextual responses
    """
    
    def __init__(self, opensearch_endpoint: str, 
                 bedrock_model_id: str = "anthropic.claude-instant-v1",
                 embedding_model_id: str = "amazon.titan-embed-text-v1"):
        """
        Initialize RAG engine
        
        Args:
            opensearch_endpoint: OpenSearch domain endpoint
            bedrock_model_id: Bedrock model for generation
            embedding_model_id: Bedrock model for embeddings
        """
        self.vector_store = OpenSearchVectorStore(opensearch_endpoint)
        self.llm = BedrockLLMService(bedrock_model_id, embedding_model_id)
    
    def query(self, user_query: str, context: ConversationContext, 
              top_k: int = 5) -> RAGResponse:
        """
        Process query using retrieval-augmented generation
        
        Args:
            user_query: User's question
            context: Conversation context
            top_k: Number of documents to retrieve
            
        Returns:
            RAG response with answer and sources
        """
        # 1. Generate embedding for query
        query_embedding = self.llm.generate_embedding(user_query)
        
        if not query_embedding:
            return RAGResponse(
                answer="I apologize, but I'm having trouble processing your query.",
                sources=[],
                confidence=0.0,
                session_id=context.session_id
            )
        
        # 2. Retrieve relevant documents with official source prioritization
        # First search for official sources
        official_results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            filters={"source_type": "official"},
            min_score=0.7
        )
        
        # If we don't have enough official sources, get general sources
        general_results = []
        if len(official_results) < top_k:
            general_results = self.vector_store.search(
                query_embedding,
                top_k=top_k - len(official_results),
                filters={"source_type": "general"},
                min_score=0.7
            )
        
        # Combine results with official sources first
        retrieved_docs = official_results + general_results
        
        if not retrieved_docs:
            return RAGResponse(
                answer="I don't have enough information to answer that question. Could you rephrase or ask about government schemes, farming, health, or skills?",
                sources=[],
                confidence=0.0,
                session_id=context.session_id
            )
        
        # 3. Build context from conversation history
        conversation_history = ""
        if context.history:
            recent_turns = context.history[-3:]  # Last 3 turns
            for turn in recent_turns:
                conversation_history += f"User: {turn.user_message}\nAssistant: {turn.assistant_message}\n\n"
        
        # 4. Construct prompt with retrieved context
        retrieved_context = "\n\n".join([
            f"[Source {i+1} - {doc['source'].get('name', 'Unknown')}]\n{doc['source'].get('description', '')}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        prompt = f"""You are BharatSahayak, a helpful AI assistant for rural India. You provide information about government schemes, farming, health, and skills in simple language.

Previous conversation:
{conversation_history if conversation_history else "This is the start of the conversation."}

Retrieved information:
{retrieved_context}

User's question: {user_query}

Instructions:
- Answer in {context.language} language if possible, otherwise use simple English
- Use the retrieved information to provide accurate answers
- If the information is not in the retrieved context, say so clearly
- Keep answers concise and practical
- Cite sources when providing specific scheme details

Answer:"""
        
        # 5. Generate response
        answer = self.llm.generate_response(prompt, max_tokens=500)
        
        # 6. Calculate confidence based on retrieval scores
        avg_score = sum(doc['score'] for doc in retrieved_docs) / len(retrieved_docs)
        confidence = min(avg_score, 1.0)
        
        # 7. Format sources
        sources = [
            {
                'scheme_id': doc['source'].get('scheme_id'),
                'name': doc['source'].get('name'),
                'category': doc['source'].get('category'),
                'relevance_score': doc['score'],
                'source_type': doc['source'].get('source_type', 'general')
            }
            for doc in retrieved_docs
        ]
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            session_id=context.session_id
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add documents to vector database
        
        Args:
            documents: List of documents with content and metadata
            
        Returns:
            Number of documents successfully indexed
        """
        indexed_count = 0
        
        for doc in documents:
            # Generate embedding for document content
            content = doc.get('content', '')
            if not content:
                continue
            
            embedding = self.llm.generate_embedding(content)
            if not embedding:
                continue
            
            # Index document
            doc_id = doc.get('id', doc.get('scheme_id'))
            metadata = {k: v for k, v in doc.items() if k not in ['content', 'id']}
            
            if self.vector_store.index_document(doc_id, content, embedding, metadata):
                indexed_count += 1
        
        return indexed_count
    
    def update_context(self, context: ConversationContext, 
                      user_query: str, response: str) -> ConversationContext:
        """
        Update conversation context with new turn
        
        Args:
            context: Current conversation context
            user_query: User's query
            response: Assistant's response
            
        Returns:
            Updated context
        """
        turn = ConversationTurn(
            user_message=user_query,
            assistant_message=response,
            timestamp=datetime.utcnow()
        )
        
        context.history.append(turn)
        context.last_activity = datetime.utcnow()
        
        return context
