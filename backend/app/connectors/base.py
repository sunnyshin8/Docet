
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup

from ..models import Document


@dataclass
class VersionInfo:
    version: str
    url: str
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class DocumentSource:
    url: str
    doc_type: str
    title: str
    description: Optional[str] = None
    versions: List[VersionInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.versions is None:
            self.versions = []


class BaseConnector(ABC):
    
    def __init__(self, url: str, **kwargs):
        self.url = url
        self.kwargs = kwargs
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Docet-Ingestion-Service/1.0',
                'Accept': 'text/html,application/json,application/xml,*/*'
            }
        )
    
    @abstractmethod
    async def detect_versions(self) -> List[VersionInfo]:
        pass
    
    @abstractmethod
    async def extract_documents_for_version(self, version_info: VersionInfo) -> List[Document]:
        pass
    
    @abstractmethod 
    def get_supported_types(self) -> List[str]:
        pass
    
    async def extract_all_documents(self) -> List[Document]:
        all_documents = []
        versions = await self.detect_versions()
        
        for version_info in versions:
            try:
                documents = await self.extract_documents_for_version(version_info)
                all_documents.extend(documents)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error extracting documents for version {version_info.version}: {str(e)}")
        
        return all_documents
    
    async def get_document_source_info(self) -> DocumentSource:
        versions = await self.detect_versions()
        
        return DocumentSource(
            url=self.url,
            doc_type=self.get_supported_types()[0] if self.get_supported_types() else 'unknown',
            title=f"Documentation from {self.url}",
            versions=versions,
            metadata={'connector': self.__class__.__name__}
        )
    
    async def fetch_content(self, url: str) -> str:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Failed to fetch content from {url}: {str(e)}")
    
    async def close(self):
        if hasattr(self, 'client'):
            await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def __del__(self):
        if hasattr(self, 'client'):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
                else:
                    asyncio.run(self.client.aclose())
            except:
                pass


class SwaggerConnector(BaseConnector):
    
    def detect_type(self) -> bool:
        return any(keyword in self.url.lower() for keyword in [
            'swagger', 'openapi', 'api-docs', '/docs'
        ])
    
    async def extract_content(self) -> List[Document]:
        try:
            content = await self.fetch_content(self.url)
            
            try:
                import json
                spec = json.loads(content)
                return await self._process_openapi_spec(spec)
            except json.JSONDecodeError:
                return await self._process_swagger_html(content)
                
        except Exception as e:
            raise Exception(f"Failed to extract Swagger content: {str(e)}")
    
    async def _process_openapi_spec(self, spec: Dict) -> List[Document]:
        documents = []
        
        info = spec.get('info', {})
        documents.append(Document(
            id=f"{self.url}#info",
            title=info.get('title', 'API Documentation'),
            content=info.get('description', ''),
            url=self.url,
            doc_type='openapi_info',
            metadata={
                'version': info.get('version'),
                'contact': info.get('contact'),
                'license': info.get('license')
            }
        ))
        
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    doc_id = f"{self.url}#{method.upper()}_{path}"
                    content = self._format_endpoint_content(path, method, details)
                    
                    documents.append(Document(
                        id=doc_id,
                        title=f"{method.upper()} {path}",
                        content=content,
                        url=self.url,
                        doc_type='openapi_endpoint',
                        metadata={
                            'path': path,
                            'method': method.upper(),
                            'tags': details.get('tags', []),
                            'operationId': details.get('operationId')
                        }
                    ))
        
        return documents
    
    async def _process_swagger_html(self, html: str) -> List[Document]:
        soup = BeautifulSoup(html, 'html.parser')
        documents = []
        
        title = soup.find('title')
        if title:
            documents.append(Document(
                id=f"{self.url}#title",
                title=title.get_text().strip(),
                content=soup.get_text(),
                url=self.url,
                doc_type='swagger_html',
                metadata={'extracted_from': 'html'}
            ))
        
        return documents
    
    def _format_endpoint_content(self, path: str, method: str, details: Dict) -> str:
        content_parts = []
        
        if 'summary' in details:
            content_parts.append(f"Summary: {details['summary']}")
        if 'description' in details:
            content_parts.append(f"Description: {details['description']}")
        
        if 'parameters' in details:
            content_parts.append("Parameters:")
            for param in details['parameters']:
                param_info = f"- {param.get('name')} ({param.get('in')}): {param.get('description', 'No description')}"
                if param.get('required'):
                    param_info += " [Required]"
                content_parts.append(param_info)
        
        if 'responses' in details:
            content_parts.append("Responses:")
            for status, response in details['responses'].items():
                content_parts.append(f"- {status}: {response.get('description', 'No description')}")
        
        return "\n".join(content_parts)


class MarkdownConnector(BaseConnector):
    
    def detect_type(self) -> bool:
        return self.url.lower().endswith('.md') or 'github.com' in self.url.lower()
    
    async def extract_content(self) -> List[Document]:
        try:
            content = await self.fetch_content(self.url)
            
            import markdown
            md = markdown.Markdown(extensions=['meta', 'toc'])
            html = md.convert(content)
            
            metadata = getattr(md, 'Meta', {})
            
            document = Document(
                id=self.url,
                title=metadata.get('title', [self.url])[0] if metadata.get('title') else self.url,
                content=content,
                url=self.url,
                doc_type='markdown',
                metadata=metadata
            )
            
            return [document]
            
        except Exception as e:
            raise Exception(f"Failed to extract Markdown content: {str(e)}")


class GenericHTMLConnector(BaseConnector):
    
    def detect_type(self) -> bool:
        return True
    
    async def extract_content(self) -> List[Document]:
        try:
            content = await self.fetch_content(self.url)
            soup = BeautifulSoup(content, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            title = soup.find('title')
            title_text = title.get_text().strip() if title else self.url
            
            text_content = soup.get_text()
            
            lines = (line.strip() for line in text_content.splitlines())
            text_content = '\n'.join(line for line in lines if line)
            
            document = Document(
                id=self.url,
                title=title_text,
                content=text_content,
                url=self.url,
                doc_type='html',
                metadata={'extracted_from': 'html'}
            )
            
            return [document]
            
        except Exception as e:
            raise Exception(f"Failed to extract HTML content: {str(e)}")


class ConnectorFactory:
    
    _connectors = [
        SwaggerConnector,
        MarkdownConnector,
        GenericHTMLConnector
    ]
    
    @classmethod
    def create_connector(cls, connector_type: str, url: str, **kwargs) -> BaseConnector:
        
        if connector_type == "swagger":
            return SwaggerConnector(url, **kwargs)
        elif connector_type == "markdown":
            return MarkdownConnector(url, **kwargs)
        elif connector_type == "html":
            return GenericHTMLConnector(url, **kwargs)
        elif connector_type == "auto":
            for connector_class in cls._connectors:
                connector = connector_class(url, **kwargs)
                if connector.detect_type():
                    return connector
            
            return GenericHTMLConnector(url, **kwargs)
        else:
            raise ValueError(f"Unsupported connector type: {connector_type}")
    
    @classmethod
    def register_connector(cls, connector_class: type):
        if issubclass(connector_class, BaseConnector):
            cls._connectors.insert(-1, connector_class)
        else:
            raise ValueError("Connector must inherit from BaseConnector")