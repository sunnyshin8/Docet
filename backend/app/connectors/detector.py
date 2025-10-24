"""Document type detection for automatic connector selection."""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DocumentTypeDetector:
    """Detects the type of documentation service from a URL."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Docet-Ingestion-Service/1.0',
                'Accept': 'text/html,application/json,application/xml,*/*'
            }
        )
    
    async def detect_document_type(self, url: str) -> Dict[str, Any]:
        """
        Detect document type and extract metadata.
        
        Returns:
            Dict containing:
            - type: Document service type (swagger, github_wiki, postman, etc.)
            - versions: List of available versions if applicable
            - metadata: Additional information about the service
            - confidence: Detection confidence score (0-1)
        """
        try:
            # Initial fetch to analyze content
            response = await self.client.get(url)
            response.raise_for_status()
            
            content = response.text
            content_type = response.headers.get('content-type', '').lower()
            
            # Check for JSON-based APIs first
            if 'application/json' in content_type:
                return await self._detect_json_api(url, content)
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Run detection methods in order of confidence
            detectors = [
                self._detect_swagger_ui,
                self._detect_redoc,
                self._detect_postman,
                self._detect_github_wiki,
                self._detect_gitbook,
                self._detect_notion,
                self._detect_confluence,
                self._detect_generic_docs
            ]
            
            for detector in detectors:
                result = await detector(url, soup, content)
                if result['confidence'] > 0.7:  # High confidence threshold
                    logger.info(f"Detected {result['type']} with confidence {result['confidence']}")
                    return result
            
            # Return best match if no high confidence detection
            results = []
            for detector in detectors:
                result = await detector(url, soup, content)
                if result['confidence'] > 0:
                    results.append(result)
            
            if results:
                best_result = max(results, key=lambda x: x['confidence'])
                logger.info(f"Best match: {best_result['type']} with confidence {best_result['confidence']}")
                return best_result
            
            # Fallback to generic HTML
            return {
                'type': 'generic_html',
                'versions': [],
                'metadata': {'title': soup.title.string if soup.title else 'Unknown'},
                'confidence': 0.1
            }
            
        except Exception as e:
            logger.error(f"Error detecting document type for {url}: {str(e)}")
            return {
                'type': 'unknown',
                'versions': [],
                'metadata': {'error': str(e)},
                'confidence': 0.0
            }
    
    async def _detect_json_api(self, url: str, content: str) -> Dict[str, Any]:
        """Detect JSON-based API specifications."""
        try:
            data = json.loads(content)
            
            # OpenAPI/Swagger specification
            if 'openapi' in data or 'swagger' in data:
                version = data.get('info', {}).get('version', '1.0.0')
                return {
                    'type': 'openapi_spec',
                    'versions': [version],
                    'metadata': {
                        'title': data.get('info', {}).get('title', 'API Documentation'),
                        'description': data.get('info', {}).get('description', ''),
                        'spec_version': data.get('openapi', data.get('swagger', 'unknown')),
                        'version': version,
                        'servers': data.get('servers', []),
                        'paths_count': len(data.get('paths', {}))
                    },
                    'confidence': 0.95
                }
            
            # Postman Collection
            elif 'info' in data and 'item' in data:
                return {
                    'type': 'postman_collection',
                    'versions': [data.get('info', {}).get('version', '1.0.0')],
                    'metadata': {
                        'title': data.get('info', {}).get('name', 'Postman Collection'),
                        'description': data.get('info', {}).get('description', ''),
                        'collection_id': data.get('info', {}).get('_postman_id'),
                        'items_count': len(data.get('item', []))
                    },
                    'confidence': 0.9
                }
            
        except json.JSONDecodeError:
            pass
        
        return {'type': 'unknown', 'versions': [], 'metadata': {}, 'confidence': 0.0}
    
    async def _detect_swagger_ui(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect Swagger UI documentation."""
        confidence = 0.0
        versions = []
        metadata = {}
        
        # Check for Swagger UI indicators
        swagger_indicators = [
            'swagger-ui',
            'swagger-container',
            'swagger.json',
            'api-docs',
            'SwaggerUIBundle'
        ]
        
        for indicator in swagger_indicators:
            if indicator in content.lower():
                confidence += 0.2
        
        # Look for version selectors
        version_selectors = soup.find_all(['select', 'div'], class_=re.compile(r'version|spec'))
        for selector in version_selectors:
            options = selector.find_all(['option', 'a'])
            for option in options:
                text = option.get_text().strip()
                if re.match(r'v?\d+\.\d+', text):
                    versions.append(text)
        
        # Look for API spec URL
        spec_urls = []
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # Look for swagger spec URLs
                spec_matches = re.findall(r'"([^"]*(?:swagger|openapi|api-docs)[^"]*\.json)"', script.string)
                spec_urls.extend(spec_matches)
        
        if spec_urls:
            confidence += 0.3
            metadata['spec_urls'] = spec_urls
        
        # Look for title
        title_elem = soup.find('title')
        if title_elem:
            metadata['title'] = title_elem.get_text().strip()
        
        return {
            'type': 'swagger_ui',
            'versions': list(set(versions)) or ['latest'],
            'metadata': metadata,
            'confidence': min(confidence, 1.0)
        }
    
    async def _detect_redoc(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect ReDoc documentation."""
        confidence = 0.0
        
        redoc_indicators = ['redoc', 'ReDoc', 'redoc-container']
        for indicator in redoc_indicators:
            if indicator in content:
                confidence += 0.3
        
        return {
            'type': 'redoc',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'ReDoc API Documentation'},
            'confidence': confidence
        }
    
    async def _detect_postman(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect Postman documentation."""
        confidence = 0.0
        
        if 'postman' in url.lower():
            confidence += 0.4
        
        postman_indicators = ['postman', 'documenter.getpostman.com', 'postman-collection']
        for indicator in postman_indicators:
            if indicator in content.lower():
                confidence += 0.2
        
        return {
            'type': 'postman_docs',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'Postman Documentation'},
            'confidence': confidence
        }
    
    async def _detect_github_wiki(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect GitHub Wiki."""
        confidence = 0.0
        
        if 'github.com' in url and '/wiki' in url:
            confidence = 0.8
        
        github_indicators = ['github.com', 'wiki', 'octicon']
        for indicator in github_indicators:
            if indicator in content.lower():
                confidence += 0.1
        
        return {
            'type': 'github_wiki',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'GitHub Wiki'},
            'confidence': min(confidence, 1.0)
        }
    
    async def _detect_gitbook(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect GitBook documentation."""
        confidence = 0.0
        
        gitbook_indicators = ['gitbook', 'GitBook', 'gitbook.io']
        for indicator in gitbook_indicators:
            if indicator in content:
                confidence += 0.3
        
        return {
            'type': 'gitbook',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'GitBook Documentation'},
            'confidence': confidence
        }
    
    async def _detect_notion(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect Notion documentation."""
        confidence = 0.0
        
        if 'notion.so' in url or 'notion.site' in url:
            confidence = 0.7
        
        notion_indicators = ['notion', 'Notion']
        for indicator in notion_indicators:
            if indicator in content:
                confidence += 0.1
        
        return {
            'type': 'notion',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'Notion Documentation'},
            'confidence': confidence
        }
    
    async def _detect_confluence(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect Confluence documentation."""
        confidence = 0.0
        
        confluence_indicators = ['confluence', 'Confluence', 'atlassian']
        for indicator in confluence_indicators:
            if indicator in content.lower():
                confidence += 0.2
        
        return {
            'type': 'confluence',
            'versions': ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'Confluence Documentation'},
            'confidence': confidence
        }
    
    async def _detect_generic_docs(self, url: str, soup: BeautifulSoup, content: str) -> Dict[str, Any]:
        """Detect generic documentation sites."""
        confidence = 0.0
        
        doc_indicators = ['documentation', 'docs', 'api', 'reference', 'guide']
        for indicator in doc_indicators:
            if indicator in url.lower() or indicator in content.lower():
                confidence += 0.1
        
        # Look for version indicators in navigation
        nav_elements = soup.find_all(['nav', 'div'], class_=re.compile(r'nav|menu|sidebar'))
        versions = []
        for nav in nav_elements:
            links = nav.find_all('a')
            for link in links:
                text = link.get_text().strip().lower()
                if re.search(r'v\d+\.\d+|version|release', text):
                    versions.append(text)
        
        return {
            'type': 'generic_docs',
            'versions': list(set(versions)) if versions else ['latest'],
            'metadata': {'title': soup.title.string if soup.title else 'Documentation'},
            'confidence': min(confidence, 0.5)  # Cap generic confidence
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()