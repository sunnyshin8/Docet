
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    OPENAPI_INFO = "openapi_info"
    OPENAPI_ENDPOINT = "openapi_endpoint"
    SWAGGER_HTML = "swagger_html"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"


class Document(BaseModel):
    
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    url: str = Field(..., description="Source URL")
    doc_type: DocumentType = Field(..., description="Type of document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    version: Optional[str] = Field(None, description="Document version")
    
    class Config:
        use_enum_values = True


class DocumentChunk(BaseModel):
    
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Index of chunk within document")
    start_char: int = Field(..., description="Start character position in original document")
    end_char: int = Field(..., description="End character position in original document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Chunk metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
    @property
    def chunk_id(self) -> str:
        return self.id
    
    class Config:
        use_enum_values = True


class ChatMessage(BaseModel):
    
    id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Chat session ID")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class ChatSession(BaseModel):
    
    id: str = Field(..., description="Unique session identifier")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")


class IngestionJob(BaseModel):
    
    id: str = Field(..., description="Unique job identifier")
    url: str = Field(..., description="Source URL")
    connector_type: str = Field(..., description="Connector type used")
    status: str = Field(..., description="Job status")
    progress: float = Field(0.0, description="Job progress (0.0 to 1.0)")
    message: str = Field("", description="Status message")
    documents_processed: int = Field(0, description="Number of documents processed")
    chunks_created: int = Field(0, description="Number of chunks created")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job metadata")


class SearchResult(BaseModel):
    
    chunk_id: str = Field(..., description="Chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Result metadata")


class EmbeddingRequest(BaseModel):
    
    text: str = Field(..., description="Text to embed")
    model: Optional[str] = Field(None, description="Embedding model to use")


class EmbeddingResponse(BaseModel):
    
    embedding: List[float] = Field(..., description="Vector embedding")
    model: str = Field(..., description="Model used for embedding")
    dimensions: int = Field(..., description="Embedding dimensions")