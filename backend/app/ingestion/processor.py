
from typing import List, Dict, Any
import re
from ..models import Document, DocumentChunk


class DocumentProcessor:
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        all_chunks = []
        
        for document in documents:
            chunks = await self.chunk_document(document)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    async def chunk_document(self, document: Document) -> List[DocumentChunk]:
        content = document.content
        chunks = []
        
        content = self._clean_content(content)
        
        chunk_texts = self._split_text(content)
        
        for i, chunk_text in enumerate(chunk_texts):
            chunk_id = f"{document.id}#chunk_{i}"
            
            start_char = i * (self.chunk_size - self.chunk_overlap)
            end_char = start_char + len(chunk_text)
            
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document.id,
                content=chunk_text,
                chunk_index=i,
                start_char=max(0, start_char),
                end_char=min(len(content), end_char),
                metadata={
                    **document.metadata,
                    'document_title': document.title,
                    'document_url': document.url,
                    'document_type': document.doc_type,
                    'chunk_size': len(chunk_text)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _clean_content(self, content: str) -> str:
        content = re.sub(r'\s+', ' ', content)
        
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', content)
        
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        return content.strip()
    
    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if start > 0 and end < len(text):
                search_start = max(start, end - self.chunk_overlap)
                sentence_break = self._find_sentence_break(text, search_start, end)
                
                if sentence_break > start:
                    end = sentence_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            if end >= len(text):
                break
            
            start = end - self.chunk_overlap
            
            if start <= chunks and len(chunks) > 0:
                start = end
        
        return chunks
    
    def _find_sentence_break(self, text: str, start: int, end: int) -> int:
        sentence_endings = r'[.!?]\s+'
        
        for match in re.finditer(sentence_endings, text[start:end]):
            return start + match.end()
        
        paragraph_breaks = r'\n\s*\n'
        for match in re.finditer(paragraph_breaks, text[start:end]):
            return start + match.end()
        
        for i in range(end - 1, start - 1, -1):
            if text[i].isspace():
                return i
        
        return end