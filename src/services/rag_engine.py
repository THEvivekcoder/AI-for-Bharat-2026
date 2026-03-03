"""
RAG Engine Service

Combines:
- OpenSearch vector search
- Bedrock embeddings + generation
- Conversation context management
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# ✅ FIXED IMPORT
from src.services.bedrock_service import BedrockService


# ===============================
# DATA MODELS
# ===============================

@dataclass
class ConversationTurn:
    user_message: str
    assistant_message: str
    timestamp: datetime


@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    language: str = "English"
    history: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RAGResponse:
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    session_id: str


# ===============================
# OPENSEARCH VECTOR STORE
# ===============================

class OpenSearchVectorStore:

    def __init__(self, endpoint: str, index_name: str = "schemes"):
        self.endpoint = endpoint
        self.index_name = index_name
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        credentials = boto3.Session().get_credentials()

        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            "es",
            session_token=credentials.token,
        )

        self.client = OpenSearch(
            hosts=[{"host": endpoint, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ):

        query_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "content_vector": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": {"excludes": ["content_vector"]}
        }

        if filters:
            filter_clauses = []
            for key, value in filters.items():
                filter_clauses.append({"term": {key: value}})

            query_body["query"] = {
                "bool": {
                    "must": [query_body["query"]],
                    "filter": filter_clauses
                }
            }

        response = self.client.search(
            index=self.index_name,
            body=query_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "source": hit["_source"]
            })

        return results


# ===============================
# RAG ENGINE
# ===============================

class RAGEngine:

    def __init__(self, opensearch_endpoint: str):
        self.vector_store = OpenSearchVectorStore(opensearch_endpoint)
        self.llm = BedrockService()

    def query(
        self,
        user_query: str,
        context: ConversationContext,
        top_k: int = 5
    ) -> RAGResponse:

        # 1️⃣ Generate embedding
        query_embedding = self.llm.generate_embedding(user_query)

        if not query_embedding:
            return RAGResponse(
                answer="I am unable to process your request right now.",
                sources=[],
                confidence=0.0,
                session_id=context.session_id
            )

        # 2️⃣ Retrieve documents
        retrieved_docs = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )

        if not retrieved_docs:
            return RAGResponse(
                answer="I couldn't find relevant scheme information.",
                sources=[],
                confidence=0.0,
                session_id=context.session_id
            )

        # 3️⃣ Build retrieved context
        retrieved_context = "\n\n".join([
            f"[{i+1}] {doc['source'].get('name', '')}\n"
            f"{doc['source'].get('description', '')}"
            for i, doc in enumerate(retrieved_docs)
        ])

        # 4️⃣ Conversation history (last 3 turns)
        history_text = ""
        for turn in context.history[-3:]:
            history_text += (
                f"User: {turn.user_message}\n"
                f"Assistant: {turn.assistant_message}\n\n"
            )

        # 5️⃣ Construct prompt
        prompt = f"""
You are BharatSahayak, an AI assistant for Indian government schemes.

Conversation history:
{history_text if history_text else "No prior conversation."}

Retrieved Information:
{retrieved_context}

User Question:
{user_query}

Instructions:
- Answer ONLY using retrieved information.
- If missing data, say clearly.
- Keep language simple.
- Respond in {context.language}.
"""

        # 6️⃣ Generate answer
        answer = self.llm.generate_response(prompt)

        # 7️⃣ Confidence score
        avg_score = sum(doc["score"] for doc in retrieved_docs) / len(retrieved_docs)

        sources = [
            {
                "scheme_id": doc["source"].get("scheme_id"),
                "name": doc["source"].get("name"),
                "relevance_score": doc["score"]
            }
            for doc in retrieved_docs
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=min(avg_score, 1.0),
            session_id=context.session_id
        )

    def update_context(
        self,
        context: ConversationContext,
        user_query: str,
        response: str
    ):

        turn = ConversationTurn(
            user_message=user_query,
            assistant_message=response,
            timestamp=datetime.utcnow()
        )

        context.history.append(turn)
        context.last_activity = datetime.utcnow()

        return context