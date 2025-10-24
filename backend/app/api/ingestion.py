"""Document ingestion API endpoints with enhanced connector support."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import asyncio
import uuid

from ..connectors.ingestion_service import get_ingestion_service
from ..vector.chroma_service import get_chroma_service
from ..rag.service import get_rag_service

router = APIRouter()


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""
    url: HttpUrl
    chatbot_id: str  # Required: which chatbot this documentation belongs to
    connector_type: Optional[str] = None  # Optional override connector type
    version: Optional[str] = None  # Optional specific version to ingest
    force_reingestion: bool = False  # Force re-ingestion even if already exists
    metadata: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    """Request model for documentation source analysis."""
    url: HttpUrl


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""
    chatbot_id: str
    url: str
    status: str  # success, failed, processing
    detected_type: Optional[str] = None
    connector_used: Optional[str] = None
    versions_processed: Optional[List[str]] = None
    total_documents: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """Response model for documentation source analysis."""
    url: str
    status: str  # supported, unsupported, error
    detected_type: Optional[str] = None
    confidence: Optional[float] = None
    connector: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    versions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SupportedSourcesResponse(BaseModel):
    """Response model for supported documentation sources."""
    total_connectors: int
    available_connectors: List[str]
    supported_types: Dict[str, Dict[str, Any]]
    auto_detection: bool
    version_aware: bool





@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_documentation_source(request: AnalysisRequest):
    """
    Analyze a documentation URL to determine type, versions, and capabilities.
    
    This endpoint helps users understand what can be ingested from a URL
    before starting the actual ingestion process.
    """
    try:
        ingestion_service = get_ingestion_service()
        result = await ingestion_service.analyze_documentation_source(str(request.url))
        
        return AnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_documentation(request: IngestionRequest):
    """
    Ingest documentation from a URL for a specific chatbot with enhanced version support.
    
    Features:
    - Automatic document type detection
    - Version-aware ingestion
    - Support for multiple documentation formats
    - Intelligent connector selection
    """
    try:
        # Validate chatbot_id
        if not request.chatbot_id or len(request.chatbot_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="chatbot_id is required")
        
        # Initialize vector service and create collection for chatbot
        vector_service = get_chroma_service()
        vector_service.create_chatbot_collection(request.chatbot_id)
        
        # Use enhanced ingestion service
        ingestion_service = get_ingestion_service()
        result = await ingestion_service.ingest_documentation(
            url=str(request.url),
            chatbot_id=request.chatbot_id,
            connector_type=request.connector_type,
            version=request.version,
            force_reingestion=request.force_reingestion
        )
        
        # Map result to response model
        response = IngestionResponse(**result)
        
        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.error or "Ingestion failed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-sources", response_model=SupportedSourcesResponse)
async def list_supported_sources():
    """
    List all supported documentation source types and their capabilities.
    
    Returns information about available connectors, supported document types,
    and example URLs for each type.
    """
    try:
        ingestion_service = get_ingestion_service()
        result = await ingestion_service.list_supported_sources()
        
        return SupportedSourcesResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.get("/chatbots")
async def list_chatbots():
    """List all chatbots with their collections."""
    try:
        vector_service = get_chroma_service()
        collections = vector_service.list_chatbot_collections()
        return {
            "chatbots": collections,
            "total": len(collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbots/{chatbot_id}/stats")
async def get_chatbot_stats(chatbot_id: str):
    """Get statistics for a specific chatbot."""
    try:
        rag_service = get_rag_service()
        stats = await rag_service.get_chatbot_knowledge_stats(chatbot_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbots/{chatbot_id}/test-retrieval")
async def test_chatbot_retrieval(chatbot_id: str, query: str):
    """Test document retrieval for a chatbot (debugging endpoint)."""
    try:
        rag_service = get_rag_service()
        results = rag_service.test_retrieval(chatbot_id, query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chatbots/{chatbot_id}")
async def delete_chatbot(chatbot_id: str):
    """Delete a chatbot and all its data."""
    try:
        vector_service = get_chroma_service()
        success = vector_service.delete_chatbot_collection(chatbot_id)
        
        if success:
            return {"message": f"Chatbot {chatbot_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete chatbot")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


