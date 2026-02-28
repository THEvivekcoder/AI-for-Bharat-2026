"""
Vector Store Service for BharatSahayak
Handles document embedding, indexing, and semantic search using FAISS
"""

import os
import pickle
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    faiss = None
    SentenceTransformer = None


@dataclass
class Document:
    """Represents a document in the knowledge base"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    source_type: str  # 'official', 'verified', 'general'
    created_at: datetime
    updated_at: datetime


@dataclass
class SearchResult:
    """Represents a search result from the vector store"""
    document: Document
    score: float
    rank: int


class VectorStore:
    """
    Vector database using FAISS for semantic search
    Handles document embedding, indexing, and retrieval
    """
    
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        index_path: Optional[str] = None,
        dimension: int = 768
    ):
        """
        Initialize vector store with embedding model
        
        Args:
            embedding_model_name: Name of sentence-transformers model
            index_path: Path to save/load FAISS index
            dimension: Dimension of embedding vectors
        """
        if faiss is None or SentenceTransformer is None:
            raise ImportError(
                "Required packages not installed. "
                "Install with: pip install faiss-cpu sentence-transformers"
            )
        
        self.embedding_model_name = embedding_model_name
        self.embedder = SentenceTransformer(embedding_model_name)
        self.dimension = dimension
        self.index_path = index_path or "data/faiss_index"
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.documents: List[Document] = []
        self.doc_id_to_idx: Dict[str, int] = {}
        
        # Load existing index if available
        if os.path.exists(f"{self.index_path}.index"):
            self.load_index()
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text
        
        Args:
            text: Input text to embed
            
        Returns:
            Normalized embedding vector
        """
        embedding = self.embedder.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of normalized embedding vectors
        """
        embeddings = self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        return embeddings
    
    def add_document(self, document: Document) -> None:
        """
        Add a single document to the vector store
        
        Args:
            document: Document to add
        """
        # Generate embedding
        embedding = self.embed_text(document.content)
        
        # Add to FAISS index
        self.index.add(embedding.reshape(1, -1))
        
        # Store document and mapping
        idx = len(self.documents)
        self.documents.append(document)
        self.doc_id_to_idx[document.doc_id] = idx
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add multiple documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        if not documents:
            return
        
        # Generate embeddings in batch
        texts = [doc.content for doc in documents]
        embeddings = self.embed_batch(texts)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store documents and mappings
        start_idx = len(self.documents)
        for i, doc in enumerate(documents):
            self.documents.append(doc)
            self.doc_id_to_idx[doc.doc_id] = start_idx + i
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        source_type_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Semantic search for documents matching query
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            source_type_filter: Filter by source types (e.g., ['official', 'verified'])
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search FAISS index
        scores, indices = self.index.search(query_embedding.reshape(1, -1), min(top_k * 2, self.index.ntotal))
        
        # Convert to SearchResult objects
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            if score < min_score:
                continue
            
            doc = self.documents[idx]
            
            # Apply source type filter
            if source_type_filter and doc.source_type not in source_type_filter:
                continue
            
            results.append(SearchResult(
                document=doc,
                score=float(score),
                rank=rank + 1
            ))
        
        # Sort by score (descending) and prioritize official sources
        results.sort(key=lambda x: (
            1 if x.document.source_type == 'official' else 0,  # Official sources first
            x.score
        ), reverse=True)
        
        # Re-rank and limit to top_k
        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1
        
        return results[:top_k]
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        idx = self.doc_id_to_idx.get(doc_id)
        if idx is not None:
            return self.documents[idx]
        return None
    
    def update_document(self, doc_id: str, updated_document: Document) -> bool:
        """
        Update an existing document
        
        Args:
            doc_id: ID of document to update
            updated_document: New document data
            
        Returns:
            True if updated, False if not found
        """
        idx = self.doc_id_to_idx.get(doc_id)
        if idx is None:
            return False
        
        # Update document
        self.documents[idx] = updated_document
        
        # Update embedding in FAISS index
        embedding = self.embed_text(updated_document.content)
        # FAISS doesn't support in-place updates, so we need to rebuild
        # For now, we'll mark this as a limitation
        # In production, consider using a database with update support
        
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store
        
        Args:
            doc_id: ID of document to delete
            
        Returns:
            True if deleted, False if not found
        """
        idx = self.doc_id_to_idx.get(doc_id)
        if idx is None:
            return False
        
        # Mark as deleted (FAISS doesn't support deletion)
        # In production, rebuild index periodically to remove deleted docs
        del self.doc_id_to_idx[doc_id]
        
        return True
    
    def save_index(self, path: Optional[str] = None) -> None:
        """
        Save FAISS index and documents to disk
        
        Args:
            path: Path to save index (without extension)
        """
        save_path = path or self.index_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{save_path}.index")
        
        # Save documents and mappings
        with open(f"{save_path}.docs", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "doc_id_to_idx": self.doc_id_to_idx,
                "embedding_model_name": self.embedding_model_name,
                "dimension": self.dimension
            }, f)
    
    def load_index(self, path: Optional[str] = None) -> None:
        """
        Load FAISS index and documents from disk
        
        Args:
            path: Path to load index from (without extension)
        """
        load_path = path or self.index_path
        
        # Load FAISS index
        self.index = faiss.read_index(f"{load_path}.index")
        
        # Load documents and mappings
        with open(f"{load_path}.docs", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.doc_id_to_idx = data["doc_id_to_idx"]
            self.embedding_model_name = data["embedding_model_name"]
            self.dimension = data["dimension"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with stats
        """
        source_type_counts = {}
        for doc in self.documents:
            source_type_counts[doc.source_type] = source_type_counts.get(doc.source_type, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal,
            "embedding_dimension": self.dimension,
            "embedding_model": self.embedding_model_name,
            "source_type_distribution": source_type_counts
        }


# Singleton instance
vector_store = VectorStore()
