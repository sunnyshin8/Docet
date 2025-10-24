
from typing import Dict, Type, List, Optional
import logging

from .base import BaseConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._type_mappings: Dict[str, str] = {}
    
    def register(self, name: str, connector_class: Type[BaseConnector]):
        if not issubclass(connector_class, BaseConnector):
            raise ValueError(f"Connector {name} must inherit from BaseConnector")

        self._connectors[name] = connector_class
        logger.info(f"Registered connector: {name}")
        
        if hasattr(connector_class, 'get_supported_types'):
            try:
                temp_instance = connector_class.__new__(connector_class)
                if hasattr(temp_instance, 'get_supported_types'):
                    supported_types = temp_instance.get_supported_types()
                    for doc_type in supported_types:
                        self._type_mappings[doc_type] = name
                        logger.info(f"Mapped document type '{doc_type}' to connector '{name}'")
            except Exception as e:
                logger.warning(f"Could not auto-register type mappings for {name}: {e}")
    
    def register_connector(self, name: str, connector_class: Type[BaseConnector], supported_types: List[str] = None):
        if not issubclass(connector_class, BaseConnector):
            raise ValueError(f"Connector {name} must inherit from BaseConnector")

        self._connectors[name] = connector_class
        logger.info(f"Registered connector: {name}")
        
        if supported_types:
            for doc_type in supported_types:
                self._type_mappings[doc_type] = name
                logger.info(f"Mapped document type '{doc_type}' to connector '{name}'")
    
    def get_connector_for_type(self, doc_type: str) -> Optional[Type[BaseConnector]]:
        connector_name = self._type_mappings.get(doc_type)
        if connector_name:
            return self._connectors.get(connector_name)
        
        fallback_mappings = {
            'swagger_ui': 'swagger',
            'openapi_spec': 'swagger', 
            'redoc': 'swagger',
            'postman_docs': 'postman',
            'postman_collection': 'postman',
            'github_wiki': 'github',
            'gitbook': 'markdown',
            'notion': 'generic',
            'confluence': 'generic',
            'generic_docs': 'generic',
            'generic_html': 'generic'
        }
        
        connector_name = fallback_mappings.get(doc_type)
        if connector_name:
            return self._connectors.get(connector_name)
        
        return None
    
    def get_connector_by_name(self, name: str) -> Optional[Type[BaseConnector]]:
        return self._connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        return list(self._connectors.keys())
    
    def list_supported_types(self) -> Dict[str, str]:
        return self._type_mappings.copy()
    
    def create_connector(self, name_or_type: str, url: str, **kwargs) -> Optional[BaseConnector]:
        connector_class = self.get_connector_by_name(name_or_type)
        
        if not connector_class:
            connector_class = self.get_connector_for_type(name_or_type)
        
        if connector_class:
            return connector_class(url, **kwargs)
        
        logger.error(f"No connector found for '{name_or_type}'")
        return None
    
    def get_registry_info(self) -> Dict[str, any]:
        return {
            'total_connectors': len(self._connectors),
            'connectors': list(self._connectors.keys()),
            'supported_types': self._type_mappings,
            'type_count': len(self._type_mappings)
        }