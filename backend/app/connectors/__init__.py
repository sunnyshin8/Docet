"""
Fivetran-style connectors for ingesting documentation from various sources.
"""

from .base import BaseConnector, ConnectorFactory, DocumentSource, VersionInfo
from .detector import DocumentTypeDetector
from .swagger_connector import SwaggerConnector
from .registry import ConnectorRegistry

# Initialize connector registry  
connector_registry = ConnectorRegistry()

# Setup default connectors
def setup_default_connectors():
    """Setup default connectors with proper type mapping."""
    # Swagger/OpenAPI connector supports multiple document types
    connector_registry.register_connector(
        'swagger', 
        SwaggerConnector,
        supported_types=[
            'swagger_ui',
            'openapi_spec', 
            'redoc'
        ]
    )

# Initialize default connectors
setup_default_connectors()

__all__ = [
    "BaseConnector",
    "ConnectorFactory", 
    "DocumentSource",
    "VersionInfo",
    "DocumentTypeDetector",
    "SwaggerConnector",
    "ConnectorRegistry",
    "connector_registry"
]