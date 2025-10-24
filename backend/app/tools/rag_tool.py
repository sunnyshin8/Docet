"""RAG documentation search tool for retrieving relevant information."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def search_documentation(query: str, chatbot_id: str = "default", limit: int = 5) -> dict:
    """
    Search the documentation database for relevant information.
    
    Args:
        query: The search query to find relevant documentation
        chatbot_id: The chatbot identifier to search within (injected from request context)
        limit: Maximum number of results to return (default: 5)
        
    Returns:
        String containing the search results with relevant documentation
    """
    try:
        # Import here to avoid circular imports
        from ..vector.chroma_service import get_chroma_service
        
        vector_service = get_chroma_service()
        
        # Search for relevant content
        results = vector_service.search_similar(
            chatbot_id=chatbot_id,
            query=query,
            limit=limit
        )
        
        if results:
            # Return structured results for programmatic consumption
            structured = []
            for result in results:
                structured.append({
                    "content": result.get('content', ''),
                    "metadata": result.get('metadata', {}),
                    "similarity_score": result.get('similarity_score', result.get('score', 0.0))
                })

            return {"query": query, "chatbot_id": chatbot_id, "results": structured}
        else:
            return {"query": query, "chatbot_id": chatbot_id, "results": []}
            
    except Exception as e:
        logger.error(f"Error searching documentation: {str(e)}")
        return f"Error searching documentation: {str(e)}"


# Gemini tool declaration
GEMINI_TOOL_DECLARATION = {
    "name": "search_documentation",
    "description": "Search the documentation database for relevant information to answer user questions",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documentation"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5, max: 10)",
                "minimum": 1,
                "maximum": 10,
                "default": 5
            }
        },
        "required": ["query"]
    }
}