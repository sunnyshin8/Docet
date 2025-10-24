"""Enhanced ingestion service with Fivetran-style connectors and version awareness."""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from .detector import DocumentTypeDetector
from .registry import ConnectorRegistry
from ..models import Document
from ..vector.chroma_service import get_chroma_service
from ..ingestion.processor import DocumentProcessor

logger = logging.getLogger(__name__)


class IngestionService:
    """Enhanced ingestion service with automatic type detection and version-aware scraping."""
    
    def __init__(self, connector_registry: ConnectorRegistry):
        self.connector_registry = connector_registry
        self.detector = DocumentTypeDetector()
        self.vector_service = get_chroma_service()
    
    async def analyze_documentation_source(self, url: str) -> Dict[str, Any]:
        """
        Analyze a documentation URL to determine type, versions, and capabilities.
        
        Returns:
            Dict with source analysis including detected type, versions, and metadata
        """
        try:
            # Detect document type and metadata
            detection_result = await self.detector.detect_document_type(url)
            
            # Get appropriate connector
            connector_class = self.connector_registry.get_connector_for_type(detection_result['type'])
            
            if not connector_class:
                return {
                    'url': url,
                    'status': 'unsupported',
                    'detected_type': detection_result['type'],
                    'confidence': detection_result['confidence'],
                    'error': f"No connector available for type: {detection_result['type']}"
                }
            
            # Create connector and analyze versions
            async with connector_class(url) as connector:
                source_info = await connector.get_document_source_info()
                
                return {
                    'url': url,
                    'status': 'supported',
                    'detected_type': detection_result['type'],
                    'confidence': detection_result['confidence'],
                    'connector': connector.__class__.__name__,
                    'title': source_info.title,
                    'description': source_info.description,
                    'versions': [
                        {
                            'version': v.version,
                            'url': v.url,
                            'is_default': v.is_default,
                            'metadata': v.metadata
                        } for v in source_info.versions
                    ],
                    'metadata': {
                        **detection_result.get('metadata', {}),
                        **source_info.metadata
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing documentation source {url}: {str(e)}")
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    async def ingest_documentation(
        self, 
        url: str, 
        chatbot_id: str,
        connector_type: Optional[str] = None,
        version: Optional[str] = None,
        force_reingestion: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest documentation with automatic type detection and version handling.
        
        Args:
            url: Documentation URL
            chatbot_id: Target chatbot identifier
            connector_type: Override connector type (optional)
            version: Specific version to ingest (optional, defaults to all versions)
            force_reingestion: Force re-ingestion even if already exists
            
        Returns:
            Dict with ingestion results and statistics
        """
        try:
            # Analyze source first
            analysis = await self.analyze_documentation_source(url)
            
            if analysis['status'] != 'supported':
                return {
                    'chatbot_id': chatbot_id,
                    'url': url,
                    'status': 'failed',
                    'error': analysis.get('error', 'Unsupported documentation type')
                }
            
            # Use override connector type if provided
            if connector_type:
                connector_class = self.connector_registry.get_connector_by_name(connector_type)
                if not connector_class:
                    return {
                        'chatbot_id': chatbot_id,
                        'url': url,
                        'status': 'failed',
                        'error': f"Unknown connector type: {connector_type}"
                    }
            else:
                connector_class = self.connector_registry.get_connector_for_type(analysis['detected_type'])
            
            # Create connector and extract documents
            async with connector_class(url) as connector:
                source_info = await connector.get_document_source_info()
                
                # Determine which versions to process
                versions_to_process = source_info.versions
                if version:
                    # Filter to specific version
                    versions_to_process = [v for v in source_info.versions if v.version == version]
                    if not versions_to_process:
                        return {
                            'chatbot_id': chatbot_id,
                            'url': url,
                            'status': 'failed',
                            'error': f"Version '{version}' not found. Available versions: {[v.version for v in source_info.versions]}"
                        }
                
                # Extract documents for each version
                all_documents = []
                version_stats = {}
                
                for version_info in versions_to_process:
                    logger.info(f"Processing version {version_info.version} for {chatbot_id}")
                    
                    try:
                        documents = await connector.extract_documents_for_version(version_info)
                        
                        # Add version tags to documents if multiple versions exist
                        if len(source_info.versions) > 1:
                            for doc in documents:
                                if 'version' not in doc.metadata:
                                    doc.metadata['version'] = version_info.version
                                doc.metadata['version_url'] = version_info.url
                                doc.metadata['is_default_version'] = version_info.is_default
                        
                        all_documents.extend(documents)
                        version_stats[version_info.version] = {
                            'documents_count': len(documents),
                            'status': 'success'
                        }
                        
                    except Exception as e:
                        logger.error(f"Error processing version {version_info.version}: {str(e)}")
                        version_stats[version_info.version] = {
                            'documents_count': 0,
                            'status': 'error',
                            'error': str(e)
                        }
                
                if not all_documents:
                    return {
                        'chatbot_id': chatbot_id,
                        'url': url,
                        'status': 'failed',
                        'error': 'No documents extracted from any version',
                        'version_stats': version_stats
                    }
                
                # Store documents in vector database
                ingestion_stats = await self._store_documents(
                    chatbot_id=chatbot_id,
                    documents=all_documents,
                    force_reingestion=force_reingestion
                )
                
                return {
                    'chatbot_id': chatbot_id,
                    'url': url,
                    'status': 'success',
                    'detected_type': analysis['detected_type'],
                    'connector_used': connector.__class__.__name__,
                    'versions_processed': list(version_stats.keys()),
                    'version_stats': version_stats,
                    'total_documents': len(all_documents),
                    'ingestion_stats': ingestion_stats,
                    'metadata': {
                        'source_title': source_info.title,
                        'source_description': source_info.description,
                        **analysis.get('metadata', {})
                    }
                }
                
        except Exception as e:
            logger.error(f"Error ingesting documentation from {url}: {str(e)}")
            return {
                'chatbot_id': chatbot_id,
                'url': url,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _store_documents(
        self, 
        chatbot_id: str, 
        documents: List[Document],
        force_reingestion: bool = False
    ) -> Dict[str, Any]:
        """Store documents in the vector database."""
        
        if force_reingestion:
            # Clear existing documents for this chatbot
            await self.vector_service.clear_chatbot_data(chatbot_id)
        
        # Process documents into chunks
        processor = DocumentProcessor()
        all_chunks = await processor.process_documents(documents)
        
        # Add chunks to vector store
        stored_count = 0
        skipped_count = 0
        error_count = 0
        chunks_stored = 0
        
        for document in documents:
            try:
                # Check if document already exists (by ID)
                if not force_reingestion:
                    existing = await self.vector_service.get_document_by_id(chatbot_id, document.id)
                    if existing:
                        skipped_count += 1
                        continue
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error checking document {document.id}: {str(e)}")
                error_count += 1
        
        # Store all chunks at once (more efficient)
        try:
            success = self.vector_service.add_documents(chatbot_id, all_chunks)
            if success:
                chunks_stored = len(all_chunks)
            else:
                error_count = len(documents)
                stored_count = 0
        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            error_count = len(documents)
            stored_count = 0
        
        return {
            'total_documents': len(documents),
            'total_chunks': len(all_chunks),
            'stored_count': stored_count,
            'chunks_stored': chunks_stored,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'force_reingestion': force_reingestion
        }
    
    async def list_supported_sources(self) -> Dict[str, Any]:
        """List all supported documentation source types."""
        registry_info = self.connector_registry.get_registry_info()
        
        # Get detailed info for each supported type
        type_details = {}
        for doc_type, connector_name in registry_info['supported_types'].items():
            connector_class = self.connector_registry.get_connector_by_name(connector_name)
            if connector_class:
                type_details[doc_type] = {
                    'connector': connector_name,
                    'description': self._get_type_description(doc_type),
                    'supports_versions': self._connector_supports_versions(connector_class),
                    'example_urls': self._get_example_urls(doc_type)
                }
        
        return {
            'total_connectors': registry_info['total_connectors'],
            'available_connectors': registry_info['connectors'],
            'supported_types': type_details,
            'auto_detection': True,
            'version_aware': True
        }
    
    def _get_type_description(self, doc_type: str) -> str:
        """Get description for a document type."""
        descriptions = {
            'swagger_ui': 'Interactive Swagger UI documentation interface',
            'openapi_spec': 'OpenAPI/Swagger JSON specification files',
            'redoc': 'ReDoc API documentation interface',
            'postman_docs': 'Postman-generated documentation pages',
            'postman_collection': 'Postman collection JSON files',
            'github_wiki': 'GitHub repository wikis',
            'gitbook': 'GitBook documentation sites',
            'notion': 'Notion documentation pages',
            'confluence': 'Atlassian Confluence spaces',
            'generic_docs': 'Generic documentation websites',
            'generic_html': 'Standard HTML documentation pages'
        }
        return descriptions.get(doc_type, 'Documentation source')
    
    def _connector_supports_versions(self, connector_class) -> bool:
        """Check if connector supports version detection."""
        # For now, assume all connectors support versions
        # This could be enhanced with a more sophisticated check
        return hasattr(connector_class, 'detect_versions')
    
    def _get_example_urls(self, doc_type: str) -> List[str]:
        """Get example URLs for a document type."""
        examples = {
            'swagger_ui': [
                'https://petstore.swagger.io/',
                'https://api.example.com/docs/',
                'https://example.com/swagger-ui/'
            ],
            'openapi_spec': [
                'https://petstore.swagger.io/v2/swagger.json',
                'https://api.example.com/openapi.json'
            ],
            'redoc': [
                'https://api.example.com/redoc/',
                'https://docs.example.com/'
            ],
            'postman_docs': [
                'https://documenter.getpostman.com/view/...'
            ],
            'github_wiki': [
                'https://github.com/user/repo/wiki'
            ]
        }
        return examples.get(doc_type, [])
    
    async def close(self):
        """Close resources."""
        await self.detector.close()


# Global ingestion service instance
_ingestion_service = None

def get_ingestion_service() -> IngestionService:
    """Get global ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        from . import connector_registry
        _ingestion_service = IngestionService(connector_registry)
    return _ingestion_service