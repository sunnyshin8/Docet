"""
ChromaDB Vector Database Service for Document Storage and Retrieval
Provides isolated collections per chatbot with embedding and similarity search
"""

import os
import uuid
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

from ..models import Document, DocumentChunk

logger = logging.getLogger(__name__)

class ChromaVectorService:
    """
    Vector database service using ChromaDB for document storage and retrieval
    Each chatbot gets its own isolated collection for data separation
    """
    
    def __init__(self, data_dir: str = "./data/chromadb"):
        """Initialize ChromaDB client and embedding model"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=data_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model (lightweight and good quality)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info(f"ChromaDB initialized at {data_dir}")
        
    def get_collection_name(self, chatbot_id: str) -> str:
        """Generate collection name for a chatbot"""
        # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens
        safe_name = f"chatbot-{chatbot_id.lower().replace('_', '-')}"
        return safe_name[:63]
    
    def create_chatbot_collection(self, chatbot_id: str) -> str:
        """Create a new collection for a chatbot"""
        collection_name = self.get_collection_name(chatbot_id)
        
        try:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"chatbot_id": chatbot_id}
            )
            logger.info(f"Created collection '{collection_name}' for chatbot {chatbot_id}")
            return collection_name
        except Exception as e:
            # Collection might already exist
            logger.warning(f"Collection creation failed (might exist): {e}")
            return collection_name
    
    def get_chatbot_collection(self, chatbot_id: str):
        """Get existing collection for a chatbot"""
        collection_name = self.get_collection_name(chatbot_id)
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection for chatbot {chatbot_id}: {e}")
            # Create collection if it doesn't exist
            self.create_chatbot_collection(chatbot_id)
            return self.client.get_collection(collection_name)
    
    def add_documents(self, chatbot_id: str, chunks: List[DocumentChunk]) -> bool:
        """Add document chunks to chatbot's collection"""
        if not chunks:
            return True
            
        collection = self.get_chatbot_collection(chatbot_id)
        
        try:
            # Prepare data for ChromaDB
            texts = [chunk.content for chunk in chunks]
            ids = [chunk.chunk_id for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False).tolist()
            
            # Prepare metadata
            metadatas = []
            for chunk in chunks:
                metadata = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "source_url": chunk.metadata.get("source_url", ""),
                    "doc_type": chunk.metadata.get("doc_type", ""),
                    "title": chunk.metadata.get("title", "")
                }
                metadatas.append(metadata)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to collection for chatbot {chatbot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to collection: {e}")
            return False
    
    def search_similar(self, chatbot_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in chatbot's collection"""
        collection = self.get_chatbot_collection(chatbot_id)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False).tolist()[0]
            
            # Search collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            if results and results['documents']:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    search_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": 1.0 - distance,  # Convert distance to similarity
                        "rank": i + 1
                    })
            
            logger.info(f"Found {len(search_results)} similar documents for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_stats(self, chatbot_id: str) -> Dict[str, Any]:
        """Get statistics for chatbot's collection"""
        try:
            collection = self.get_chatbot_collection(chatbot_id)
            count = collection.count()
            
            return {
                "chatbot_id": chatbot_id,
                "collection_name": self.get_collection_name(chatbot_id),
                "document_count": count,
                "embedding_model": "all-MiniLM-L6-v2"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"chatbot_id": chatbot_id, "error": str(e)}
    
    async def clear_chatbot_data(self, chatbot_id: str) -> bool:
        """Clear all data for a chatbot (recreate collection)"""
        collection_name = self.get_collection_name(chatbot_id)
        
        try:
            # Delete existing collection
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"Cleared existing collection for chatbot {chatbot_id}")
            except Exception:
                pass  # Collection might not exist
            
            # Recreate collection
            self.create_chatbot_collection(chatbot_id)
            return True
        except Exception as e:
            logger.error(f"Failed to clear chatbot data: {e}")
            return False
    
    async def get_document_by_id(self, chatbot_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        collection_name = self.get_collection_name(chatbot_id)
        
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.get(ids=[document_id])
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0] if results['documents'] else None,
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def add_document(self, chatbot_id: str, document: Document) -> bool:
        """Add a single document to the chatbot's collection"""
        try:
            return self.add_documents(chatbot_id, [document])
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    def delete_chatbot_collection(self, chatbot_id: str) -> bool:
        """Delete entire collection for a chatbot"""
        collection_name = self.get_collection_name(chatbot_id)
        
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}' for chatbot {chatbot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def list_chatbot_collections(self) -> List[Dict[str, str]]:
        """List all chatbot collections"""
        try:
            collections = self.client.list_collections()
            
            chatbot_collections = []
            for collection in collections:
                if collection.name.startswith("chatbot-"):
                    metadata = collection.metadata or {}
                    chatbot_collections.append({
                        "collection_name": collection.name,
                        "chatbot_id": metadata.get("chatbot_id", "unknown"),
                        "document_count": collection.count()
                    })
            
            return chatbot_collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

# Global service instance
_chroma_service = None

def get_chroma_service() -> ChromaVectorService:
    """Get global ChromaDB service instance"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaVectorService()
    return _chroma_service