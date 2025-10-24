"""
RAG (Retrieval-Augmented Generation) Service
Combines vector search with language model generation for intelligent responses
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union
from ..vector.chroma_service import get_chroma_service
from ..llm.gemini_service import get_gemini_llm_service
from ..tools import get_tool_function, is_tool_allowed_for_chatbot

logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG service that retrieves relevant documents and generates responses
    Uses ChromaDB for retrieval and Gemini for generation
    """
    
    def __init__(self):
        self.vector_service = get_chroma_service()
        self.llm_service = get_gemini_llm_service()
        
    async def generate_response(
        self, 
        chatbot_id: str, 
        query: str, 
        session_id: Optional[str] = None,
        max_context_chunks: int = 8  # Increased for better context
    ) -> Dict[str, Any]:
        """
        Generate response using RAG pipeline:
        1. Retrieve relevant documents from vector DB
        2. Create context from retrieved documents  
        3. Generate response using LLM with context
        """
        
        # Step 1: Ask Gemini to produce a retrieval query by invoking the search tool
        logger.info(f"Requesting Gemini to generate a retrieval query for chatbot {chatbot_id} (user query preview: {query[:100]})")

        # Prompt Gemini to generate a concise retrieval query and call the tool
        retrieval_prompt = f"""
You are a search planner for an API documentation assistant.
User asked: "{query}"

Produce a concise search query that will return relevant documentation sections (endpoints, operations, descriptions) which can be used to answer the user's question. Call the tool `search_documentation` with the generated query.

Only call the tool with a short, focused query string.
"""

        # Request function call metadata instead of executing it directly
        llm_action = await self.llm_service.generate_response(
            prompt=retrieval_prompt,
            chatbot_id=chatbot_id,
            session_id=session_id or f"{chatbot_id}:retrieval",
            return_function_call=True
        )

        search_results = None

        # If LLM returned a function call action, execute the corresponding tool
        if isinstance(llm_action, dict) and llm_action.get("action") == "function_call":
            func_name = llm_action.get("function_name")
            func_args = llm_action.get("function_args", {})
            logger.info(f"LLM requested tool '{func_name}' with args: {func_args}")

            # Only allow approved tools
            if not is_tool_allowed_for_chatbot(func_name, chatbot_id):
                logger.warning(f"Tool {func_name} not allowed for chatbot {chatbot_id}")
            else:
                tool_fn = get_tool_function(func_name)
                if tool_fn:
                    # Inject chatbot_id if needed
                    if 'chatbot_id' in tool_fn.__code__.co_varnames:
                        func_args['chatbot_id'] = chatbot_id

                    try:
                        tool_result = tool_fn(**func_args)
                        # Expect structured result {results: [...]}
                        if isinstance(tool_result, dict) and 'results' in tool_result:
                            search_results = tool_result['results']
                        else:
                            # Fall back to vector search if tool returns text or unexpected format
                            logger.info("Tool returned non-structured results, falling back to vector search")
                            search_results = self.vector_service.search_similar(chatbot_id=chatbot_id, query=query, limit=max_context_chunks)
                    except Exception as e:
                        logger.error(f"Error executing tool {func_name}: {e}")
                        search_results = self.vector_service.search_similar(chatbot_id=chatbot_id, query=query, limit=max_context_chunks)

        else:
            # Fallback: direct vector search using original user query
            logger.info("LLM did not return a function action; using direct vector search")
            search_results = self.vector_service.search_similar(chatbot_id=chatbot_id, query=query, limit=max_context_chunks)

        if not search_results:
            logger.warning(f"No relevant documents found for chatbot {chatbot_id}")
            return {
                "response": "I don't have any relevant information to answer your question. Please make sure the API documentation has been ingested for this chatbot.",
                "sources": [],
                "context_used": False,
                "session_id": session_id
            }
        
        # Step 2: Build context from retrieved documents
        context_chunks = []
        sources = []
        
        for result in search_results:
            # Only use relevant results (similarity > 0.1)
            if result.get("similarity_score", 0) > 0.1:
                context_chunks.append(result["content"])
                
                # Track sources for transparency
                metadata = result.get("metadata", {})
                source_info = {
                    "title": metadata.get("title", "Unknown"),
                    "url": metadata.get("source_url", ""),
                    "similarity": round(result.get("similarity_score", 0), 3)
                }
                sources.append(source_info)
        
        # Step 3: Create prompt with context
        if context_chunks:
            context_text = "\n\n".join(context_chunks[:max_context_chunks])
            
            # Create enhanced RAG prompt 
            rag_prompt = self._create_enhanced_rag_prompt(query, context_text)
            
            logger.info(f"Using {len(context_chunks)} context chunks for response generation")
            
            # Generate response with context
            llm_response = await self.llm_service.generate_response(
                prompt=rag_prompt,
                chatbot_id=chatbot_id,
                session_id=session_id or f"{chatbot_id}:default"
            )
            
            # Handle different response types
            if isinstance(llm_response, dict):
                # Handle action requests (more context, tool usage)
                return await self._handle_action_request(llm_response, chatbot_id, query, session_id)
            else:
                # Regular text response
                return {
                    "response": llm_response,
                    "sources": sources,
                    "context_used": True,
                    "context_chunks_count": len(context_chunks),
                    "session_id": session_id
                }
        
        else:
            # No relevant context found - suggest more specific query
            logger.info("No sufficiently relevant context found, suggesting query refinement")
            
            general_prompt = self._create_no_context_prompt(query)
            
            general_response = await self.llm_service.generate_response(
                prompt=general_prompt,
                chatbot_id=chatbot_id,
                session_id=session_id or f"{chatbot_id}:default"
            )
            
            # Handle action requests even without context
            if isinstance(general_response, dict):
                return await self._handle_action_request(general_response, chatbot_id, query, session_id)
            
            return {
                "response": general_response,
                "sources": [],
                "context_used": False,
                "session_id": session_id,
                "suggestion": "Try being more specific or use different keywords related to the API."
            }
    
    def _create_enhanced_rag_prompt(self, query: str, context: str) -> str:
        """Create enhanced RAG prompt with context"""
        
        prompt = f"""You are an expert API assistant helping developers understand and use APIs effectively.

API DOCUMENTATION CONTEXT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer the user's question based on the provided API documentation context
2. Be specific, accurate, and helpful
3. Include relevant code examples when helpful
4. Reference specific parts of the documentation when applicable
5. Use available tools when needed to provide additional information

RESPONSE:"""
        
        return prompt
    
    def _create_no_context_prompt(self, query: str) -> str:
        """Create prompt when no relevant context is found"""
        
        prompt = f"""You are an expert API assistant. A user asked: "{query}"

No relevant documentation was found for this query.

INSTRUCTIONS:
1. Provide a helpful response explaining what information you would need
2. Use available tools to help answer the question if possible
3. Suggest how the user might rephrase their question to get better results

RESPONSE:"""
        
        return prompt
    
    async def _handle_action_request(self, action_response: Dict[str, Any], chatbot_id: str, original_query: str, session_id: Optional[str]) -> Dict[str, Any]:
        """Handle action requests from Gemini (more context, tool usage, etc.)"""
        
        action = action_response.get("action")
        
        if action == "request_more_context":
            # Get more context with refined query
            new_query = action_response.get("query", original_query)
            logger.info(f"Gemini requested more context with query: {new_query}")
            
            # Search again with refined query
            refined_results = self.vector_service.search_similar(
                chatbot_id=chatbot_id,
                query=new_query,
                limit=10  # More results for refined search
            )
            
            if refined_results:
                # Try again with new context
                return await self.generate_response(chatbot_id, original_query, session_id, max_context_chunks=10)
            else:
                return {
                    "response": f"I couldn't find relevant information in the documentation for '{original_query}'. The documentation may not cover this topic, or you might need to rephrase your question with different keywords.",
                    "sources": [],
                    "context_used": False,
                    "session_id": session_id,
                    "action_attempted": "request_more_context",
                    "refined_query": new_query
                }
        
        else:
            # Unknown action - just return the response as is
            return {
                "response": f"I tried to perform an action but encountered an unknown request type. Please rephrase your question.",
                "sources": [],
                "context_used": False,
                "session_id": session_id,
                "unknown_action": action_response
            }
    
    async def get_chatbot_knowledge_stats(self, chatbot_id: str) -> Dict[str, Any]:
        """Get statistics about chatbot's knowledge base"""
        
        # Get collection stats from vector DB
        collection_stats = self.vector_service.get_collection_stats(chatbot_id)
        
        # Get LLM service info
        llm_info = await self.llm_service.get_model_info()
        
        return {
            "chatbot_id": chatbot_id,
            "vector_db": collection_stats,
            "llm_service": llm_info,
            "rag_enabled": True,
            "enhanced_features": {
                "context_requests": True,
                "tool_usage": True,
                "dynamic_search": True,
                "session_management": True
            }
        }
    
    def test_retrieval(self, chatbot_id: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Test document retrieval without generating response (for debugging)"""
        
        search_results = self.vector_service.search_similar(
            chatbot_id=chatbot_id,
            query=query,
            limit=limit
        )
        
        return {
            "query": query,
            "results_count": len(search_results),
            "results": search_results
        }

# Global RAG service instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service