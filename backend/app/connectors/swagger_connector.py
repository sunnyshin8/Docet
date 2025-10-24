import json
import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

from .base import BaseConnector, DocumentSource, VersionInfo
from ..models import Document

logger = logging.getLogger(__name__)


class SwaggerConnector(BaseConnector):
    
    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        self.detected_type = None
        self.available_versions = []
        self.spec_urls = {}
    
    def get_supported_types(self) -> List[str]:
        return ['swagger_ui', 'openapi_spec', 'redoc']
    
    async def detect_versions(self) -> List[VersionInfo]:
        try:
            response = await self.client.get(self.url)
            response.raise_for_status()
            content = response.text
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                return await self._detect_versions_from_spec(content)
            
            soup = BeautifulSoup(content, 'html.parser')
            return await self._detect_versions_from_ui(soup, content)
            
        except Exception as e:
            logger.error(f"Error detecting versions for {self.url}: {str(e)}")
            return [VersionInfo(version='latest', url=self.url, is_default=True)]
    
    async def _detect_versions_from_spec(self, content: str) -> List[VersionInfo]:
        try:
            spec = json.loads(content)
            version = spec.get('info', {}).get('version', '1.0.0')
            
            return [VersionInfo(
                version=version,
                url=self.url,
                is_default=True,
                metadata={
                    'title': spec.get('info', {}).get('title'),
                    'description': spec.get('info', {}).get('description'),
                    'spec_version': spec.get('openapi', spec.get('swagger'))
                }
            )]
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in OpenAPI spec: {self.url}")
            return []
    
    async def _detect_versions_from_ui(self, soup: BeautifulSoup, content: str) -> List[VersionInfo]:
        versions = []
        
        version_selectors = soup.find_all(['select', 'div'], class_=re.compile(r'version|spec|api'))
        for selector in version_selectors:
            options = selector.find_all(['option', 'a', 'button'])
            for option in options:
                text = option.get_text().strip()
                href = option.get('href') or option.get('value')
                
                if re.match(r'v?\d+\.\d+(\.\d+)?', text):
                    spec_url = self._resolve_spec_url(href) if href else self.url
                    versions.append(VersionInfo(
                        version=text,
                        url=spec_url,
                        is_default=len(versions) == 0,
                        metadata={'source': 'version_selector'}
                    ))
        
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                spec_matches = re.findall(
                    r'(?:url|spec)\\?["\']\\?:\\s*["\']([^"\']+(?:swagger|openapi|api-docs)[^"\']*\.json[^"\']*)["\']',
                    script.string
                )
                
                for spec_url in spec_matches:
                    spec_url = self._resolve_spec_url(spec_url)
                    version_match = re.search(r'v(\d+(?:\.\d+)*)', spec_url)
                    version = version_match.group(1) if version_match else 'latest'
                    
                    if not any(v.version == version for v in versions):
                        versions.append(VersionInfo(
                            version=version,
                            url=spec_url,
                            is_default=len(versions) == 0,
                            metadata={'source': 'javascript_config'}
                        ))
        
        if not versions:
            common_paths = [
                '/swagger.json',
                '/openapi.json',
                '/api-docs',
                '/v1/swagger.json',
                '/v2/swagger.json',
                '/v3/swagger.json'
            ]
            
            base_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
            for path in common_paths:
                spec_url = urljoin(base_url, path)
                if await self._test_spec_url(spec_url):
                    version_match = re.search(r'v(\d+)', path)
                    version = version_match.group(1) if version_match else 'latest'
                    
                    versions.append(VersionInfo(
                        version=version,
                        url=spec_url,
                        is_default=len(versions) == 0,
                        metadata={'source': 'common_paths'}
                    ))
        
        if not versions:
            versions.append(VersionInfo(
                version='latest',
                url=self.url,
                is_default=True,
                metadata={'source': 'fallback'}
            ))
        
        return versions
    
    async def _test_spec_url(self, url: str) -> bool:
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                content = response.text
                data = json.loads(content)
                return 'openapi' in data or 'swagger' in data or 'paths' in data
        except:
            pass
        return False
    
    def _resolve_spec_url(self, url: str) -> str:
        if url.startswith('http'):
            return url
        return urljoin(self.url, url)
    
    async def extract_documents_for_version(self, version_info: VersionInfo) -> List[Document]:
        try:
            response = await self.client.get(version_info.url)
            response.raise_for_status()
            content = response.text
            
            try:
                spec = json.loads(content)
                return await self._extract_from_openapi_spec(spec, version_info)
            except json.JSONDecodeError:
                return await self._extract_from_html(content, version_info)
                
        except Exception as e:
            logger.error(f"Error extracting documents for version {version_info.version}: {str(e)}")
            return []
    
    async def _extract_from_openapi_spec(self, spec: Dict, version_info: VersionInfo) -> List[Document]:
        documents = []
        version = version_info.version
        
        info = spec.get('info', {})
        documents.append(Document(
            id=f"{self.url}#{version}#info",
            title=f"{info.get('title', 'API Documentation')} (v{version})",
            content=self._format_api_info(info, spec),
            url=version_info.url,
            doc_type='openapi_info',
            metadata={
                'version': version,
                'api_version': info.get('version'),
                'contact': info.get('contact'),
                'license': info.get('license'),
                'servers': spec.get('servers', []),
                'source_type': 'openapi_spec'
            }
        ))
        
        servers = spec.get('servers', [])
        if servers:
            server_content = self._format_server_info(servers)
            documents.append(Document(
                id=f"{self.url}#{version}#servers",
                title=f"API Servers (v{version})",
                content=server_content,
                url=version_info.url,
                doc_type='openapi_servers',
                metadata={'version': version, 'servers': servers}
            ))
        
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        if security_schemes:
            security_content = self._format_security_info(security_schemes)
            documents.append(Document(
                id=f"{self.url}#{version}#security",
                title=f"Authentication & Security (v{version})",
                content=security_content,
                url=version_info.url,
                doc_type='openapi_security',
                metadata={'version': version, 'security_schemes': list(security_schemes.keys())}
            ))
        
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']:
                    doc_id = f"{self.url}#{version}#{method.upper()}_{path}"
                    content = self._format_endpoint_content(path, method, details, spec)
                    
                    documents.append(Document(
                        id=doc_id,
                        title=f"{method.upper()} {path} (v{version})",
                        content=content,
                        url=version_info.url,
                        doc_type='openapi_endpoint',
                        metadata={
                            'version': version,
                            'path': path,
                            'method': method.upper(),
                            'tags': details.get('tags', []),
                            'operationId': details.get('operationId'),
                            'deprecated': details.get('deprecated', False)
                        }
                    ))
        
        schemas = components.get('schemas', {})
        for schema_name, schema_def in schemas.items():
            content = self._format_schema_content(schema_name, schema_def)
            documents.append(Document(
                id=f"{self.url}#{version}#schema_{schema_name}",
                title=f"Schema: {schema_name} (v{version})",
                content=content,
                url=version_info.url,
                doc_type='openapi_schema',
                metadata={
                    'version': version,
                    'schema_name': schema_name,
                    'schema_type': schema_def.get('type')
                }
            ))
        
        return documents
    
    async def _extract_from_html(self, content: str, version_info: VersionInfo) -> List[Document]:
        soup = BeautifulSoup(content, 'html.parser')
        
        for element in soup(['script', 'style']):
            element.decompose()
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else f"API Documentation (v{version_info.version})"
        
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        text_content = '\\n'.join(line for line in lines if line)
        
        document = Document(
            id=f"{self.url}#{version_info.version}#html",
            title=title_text,
            content=text_content,
            url=version_info.url,
            doc_type='swagger_html',
            metadata={
                'version': version_info.version,
                'extracted_from': 'html',
                'source_type': 'html_documentation'
            }
        )
        
        return [document]
    
    def _format_api_info(self, info: Dict, spec: Dict) -> str:
        content_parts = []
        
        if info.get('title'):
            content_parts.append(f"# {info['title']}")
        
        if info.get('description'):
            content_parts.append(f"## Description\\n{info['description']}")
        
        if info.get('version'):
            content_parts.append(f"**Version:** {info['version']}")
        
        if spec.get('openapi'):
            content_parts.append(f"**OpenAPI Version:** {spec['openapi']}")
        elif spec.get('swagger'):
            content_parts.append(f"**Swagger Version:** {spec['swagger']}")
        
        contact = info.get('contact', {})
        if contact:
            contact_info = []
            if contact.get('name'):
                contact_info.append(f"**Contact:** {contact['name']}")
            if contact.get('email'):
                contact_info.append(f"**Email:** {contact['email']}")
            if contact.get('url'):
                contact_info.append(f"**URL:** {contact['url']}")
            if contact_info:
                content_parts.extend(contact_info)
        
        license_info = info.get('license', {})
        if license_info:
            if license_info.get('name'):
                content_parts.append(f"**License:** {license_info['name']}")
            if license_info.get('url'):
                content_parts.append(f"**License URL:** {license_info['url']}")
        
        return '\\n\\n'.join(content_parts)
    
    def _format_server_info(self, servers: List[Dict]) -> str:
        content_parts = ["# API Servers"]
        
        for i, server in enumerate(servers, 1):
            content_parts.append(f"## Server {i}")
            content_parts.append(f"**URL:** {server.get('url', 'N/A')}")
            
            if server.get('description'):
                content_parts.append(f"**Description:** {server['description']}")
            
            variables = server.get('variables', {})
            if variables:
                content_parts.append("**Variables:**")
                for var_name, var_info in variables.items():
                    var_desc = var_info.get('description', 'No description')
                    default_val = var_info.get('default', 'No default')
                    content_parts.append(f"- {var_name}: {var_desc} (default: {default_val})")
        
        return '\\n'.join(content_parts)
    
    def _format_security_info(self, security_schemes: Dict) -> str:
        content_parts = ["# Authentication & Security"]
        
        for scheme_name, scheme_info in security_schemes.items():
            content_parts.append(f"## {scheme_name}")
            content_parts.append(f"**Type:** {scheme_info.get('type', 'Unknown')}")
            
            if scheme_info.get('description'):
                content_parts.append(f"**Description:** {scheme_info['description']}")
            
            scheme_type = scheme_info.get('type')
            if scheme_type == 'apiKey':
                content_parts.append(f"**Location:** {scheme_info.get('in', 'N/A')}")
                content_parts.append(f"**Parameter Name:** {scheme_info.get('name', 'N/A')}")
            elif scheme_type == 'http':
                content_parts.append(f"**Scheme:** {scheme_info.get('scheme', 'N/A')}")
                if scheme_info.get('bearerFormat'):
                    content_parts.append(f"**Bearer Format:** {scheme_info['bearerFormat']}")
            elif scheme_type == 'oauth2':
                flows = scheme_info.get('flows', {})
                if flows:
                    content_parts.append("**OAuth2 Flows:**")
                    for flow_type, flow_info in flows.items():
                        content_parts.append(f"- {flow_type}: {flow_info.get('authorizationUrl', 'N/A')}")
        
        return '\\n'.join(content_parts)
    
    def _format_endpoint_content(self, path: str, method: str, details: Dict, spec: Dict) -> str:
        content_parts = []
        
        content_parts.append(f"# {method.upper()} {path}")
        
        if details.get('summary'):
            content_parts.append(f"## Summary\\n{details['summary']}")
        
        if details.get('description'):
            content_parts.append(f"## Description\\n{details['description']}")
        
        tags = details.get('tags', [])
        if tags:
            content_parts.append(f"**Tags:** {', '.join(tags)}")
        
        if details.get('operationId'):
            content_parts.append(f"**Operation ID:** {details['operationId']}")
        
        if details.get('deprecated'):
            content_parts.append("**⚠️ DEPRECATED**")
        
        parameters = details.get('parameters', [])
        if parameters:
            content_parts.append("## Parameters")
            for param in parameters:
                param_name = param.get('name', 'Unknown')
                param_in = param.get('in', 'Unknown')
                param_desc = param.get('description', 'No description')
                required = " [Required]" if param.get('required') else ""
                
                param_schema = param.get('schema', {})
                param_type = param_schema.get('type', 'Unknown')
                
                content_parts.append(f"- **{param_name}** ({param_in}): {param_desc} - Type: {param_type}{required}")
        
        request_body = details.get('requestBody', {})
        if request_body:
            content_parts.append("## Request Body")
            if request_body.get('description'):
                content_parts.append(request_body['description'])
            
            content_types = list(request_body.get('content', {}).keys())
            if content_types:
                content_parts.append(f"**Content Types:** {', '.join(content_types)}")
        
        responses = details.get('responses', {})
        if responses:
            content_parts.append("## Responses")
            for status_code, response in responses.items():
                desc = response.get('description', 'No description')
                content_parts.append(f"- **{status_code}**: {desc}")
                
                content_types = list(response.get('content', {}).keys())
                if content_types:
                    content_parts.append(f"  - Content Types: {', '.join(content_types)}")
        
        return '\\n\\n'.join(content_parts)
    
    def _format_schema_content(self, schema_name: str, schema_def: Dict) -> str:
        content_parts = [f"# Schema: {schema_name}"]
        
        if schema_def.get('description'):
            content_parts.append(f"## Description\\n{schema_def['description']}")
        
        schema_type = schema_def.get('type')
        if schema_type:
            content_parts.append(f"**Type:** {schema_type}")
        
        properties = schema_def.get('properties', {})
        if properties:
            content_parts.append("## Properties")
            required_props = set(schema_def.get('required', []))
            
            for prop_name, prop_def in properties.items():
                prop_type = prop_def.get('type', 'Unknown')
                prop_desc = prop_def.get('description', 'No description')
                required_marker = " [Required]" if prop_name in required_props else ""
                
                content_parts.append(f"- **{prop_name}** ({prop_type}): {prop_desc}{required_marker}")
        
        if schema_type == 'array' and 'items' in schema_def:
            items_def = schema_def['items']
            if '$ref' in items_def:
                ref_name = items_def['$ref'].split('/')[-1]
                content_parts.append(f"**Array Items:** {ref_name}")
            else:
                items_type = items_def.get('type', 'Unknown')
                content_parts.append(f"**Array Items Type:** {items_type}")
        
        enum_values = schema_def.get('enum')
        if enum_values:
            content_parts.append(f"**Possible Values:** {', '.join(map(str, enum_values))}")
        
        return '\\n\\n'.join(content_parts)