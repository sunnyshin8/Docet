
import os
import json
import pickle
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiofiles

from ..config import settings
from ..models import Document, DocumentChunk


class LocalStorageService:
    
    def __init__(self):
        self.documents_path = os.path.join(settings.LOCAL_STORAGE_PATH, "documents")
        self.chunks_path = os.path.join(settings.LOCAL_STORAGE_PATH, "chunks")
        self.embeddings_path = os.path.join(settings.LOCAL_STORAGE_PATH, "embeddings")
        self.mapping_file = os.path.join(settings.LOCAL_STORAGE_PATH, "id_mapping.json")
        
        os.makedirs(self.documents_path, exist_ok=True)
        os.makedirs(self.chunks_path, exist_ok=True)
        os.makedirs(self.embeddings_path, exist_ok=True)
        
        self.id_mapping = self._load_id_mapping()
    
    def _sanitize_filename(self, filename: str) -> str:
        replacements = {
            '/': '_slash_',
            '\\': '_backslash_',
            ':': '_colon_',
            '*': '_star_',
            '?': '_question_',
            '"': '_quote_',
            '<': '_lt_',
            '>': '_gt_',
            '|': '_pipe_',
            '#': '_hash_',
            '{': '_lbrace_',
            '}': '_rbrace_',
            '[': '_lbracket_',
            ']': '_rbracket_',
            ' ': '_space_'
        }
        
        safe_filename = filename
        for char, replacement in replacements.items():
            safe_filename = safe_filename.replace(char, replacement)
        
        if len(safe_filename) > 200:
            safe_filename = safe_filename[:200]
        
        return safe_filename
    
    def _load_id_mapping(self) -> Dict[str, str]:
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading ID mapping: {str(e)}")
        return {}
    
    def _save_id_mapping(self):
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.id_mapping, f, indent=2)
        except Exception as e:
            print(f"Error saving ID mapping: {str(e)}")
    
    def _get_safe_filename(self, original_id: str) -> str:
        if original_id not in self.id_mapping:
            safe_filename = self._sanitize_filename(original_id)
            self.id_mapping[original_id] = safe_filename
            self._save_id_mapping()
        return self.id_mapping[original_id]
    
    async def save_document(self, document: Document) -> bool:
        try:
            safe_filename = self._get_safe_filename(document.id)
            file_path = os.path.join(self.documents_path, f"{safe_filename}.json")
            
            doc_dict = document.dict()
            doc_dict['created_at'] = doc_dict['created_at'].isoformat() if doc_dict['created_at'] else None
            doc_dict['updated_at'] = doc_dict['updated_at'].isoformat() if doc_dict['updated_at'] else None
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(doc_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Error saving document {document.id}: {str(e)}")
            return False
    
    async def load_document(self, document_id: str) -> Optional[Document]:
        try:
            safe_filename = self._get_safe_filename(document_id)
            file_path = os.path.join(self.documents_path, f"{safe_filename}.json")
            
            if not os.path.exists(file_path):
                return None
            
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                doc_dict = json.loads(content)
            
            if doc_dict.get('created_at'):
                doc_dict['created_at'] = datetime.fromisoformat(doc_dict['created_at'])
            if doc_dict.get('updated_at'):
                doc_dict['updated_at'] = datetime.fromisoformat(doc_dict['updated_at'])
            
            return Document(**doc_dict)
        except Exception as e:
            print(f"Error loading document {document_id}: {str(e)}")
            return None
    
    async def list_documents(self) -> List[Document]:
        documents = []
        try:
            for filename in os.listdir(self.documents_path):
                if filename.endswith('.json'):
                    document_id = filename[:-5]
                    doc = await self.load_document(document_id)
                    if doc:
                        documents.append(doc)
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
        
        return documents
    
    async def save_chunks(self, chunks: List[DocumentChunk]) -> bool:
        try:
            for chunk in chunks:
                safe_filename = self._get_safe_filename(chunk.id)
                file_path = os.path.join(self.chunks_path, f"{safe_filename}.json")
                
                chunk_dict = chunk.dict()
                
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(json.dumps(chunk_dict, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            print(f"Error saving chunks: {str(e)}")
            return False
    
    async def load_chunks(self, document_id: str) -> List[DocumentChunk]:
        chunks = []
        try:
            for filename in os.listdir(self.chunks_path):
                if filename.endswith('.json'):
                    async with aiofiles.open(os.path.join(self.chunks_path, filename), 'r') as f:
                        content = await f.read()
                        chunk_dict = json.loads(content)
                    
                    if chunk_dict.get('document_id') == document_id:
                        chunks.append(DocumentChunk(**chunk_dict))
        except Exception as e:
            print(f"Error loading chunks for document {document_id}: {str(e)}")
        
        return chunks
    
    async def save_embeddings(self, embeddings: Dict[str, List[float]]) -> bool:
        try:
            file_path = os.path.join(self.embeddings_path, "embeddings.pkl")
            
            with open(file_path, 'wb') as f:
                pickle.dump(embeddings, f)
            
            return True
        except Exception as e:
            print(f"Error saving embeddings: {str(e)}")
            return False
    
    async def load_embeddings(self) -> Dict[str, List[float]]:
        try:
            file_path = os.path.join(self.embeddings_path, "embeddings.pkl")
            
            if not os.path.exists(file_path):
                return {}
            
            with open(file_path, 'rb') as f:
                embeddings = pickle.load(f)
            
            return embeddings
        except Exception as e:
            print(f"Error loading embeddings: {str(e)}")
            return {}
    
    async def delete_document(self, document_id: str) -> bool:
        try:
            safe_filename = self._get_safe_filename(document_id)
            doc_path = os.path.join(self.documents_path, f"{safe_filename}.json")
            if os.path.exists(doc_path):
                os.remove(doc_path)
            
            for filename in os.listdir(self.chunks_path):
                if filename.endswith('.json'):
                    chunk_path = os.path.join(self.chunks_path, filename)
                    async with aiofiles.open(chunk_path, 'r') as f:
                        content = await f.read()
                        chunk_dict = json.loads(content)
                    
                    if chunk_dict.get('document_id') == document_id:
                        os.remove(chunk_path)
            
            if document_id in self.id_mapping:
                del self.id_mapping[document_id]
                self._save_id_mapping()
            
            return True
        except Exception as e:
            print(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        try:
            doc_count = len([f for f in os.listdir(self.documents_path) if f.endswith('.json')])
            chunk_count = len([f for f in os.listdir(self.chunks_path) if f.endswith('.json')])
            
            total_size = 0
            for root, dirs, files in os.walk(settings.LOCAL_STORAGE_PATH):
                total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
            
            return {
                "documents": doc_count,
                "chunks": chunk_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": settings.LOCAL_STORAGE_PATH
            }
        except Exception as e:
            print(f"Error getting storage stats: {str(e)}")
            return {"error": str(e)}


local_storage_service = LocalStorageService()