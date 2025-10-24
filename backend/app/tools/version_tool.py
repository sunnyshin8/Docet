"""Version information tool for retrieving API version details from documentation."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_api_version_info(chatbot_id: str = "default") -> str:
    """
    Get API version information from the documentation database.
    
    Args:
        chatbot_id: The chatbot identifier to search for version info (injected from request context)
        
    Returns:
        String containing version information found in documentation
    """
    try:
        # Import here to avoid circular imports
        from ..vector.chroma_service import get_chroma_service
        
        vector_service = get_chroma_service()
        
        # Search for version-related content
        version_queries = [
            "API version versions supported",
            "v1 v2 v3 version compatibility",
            "current version latest version"
        ]
        
        all_results = []
        for query in version_queries:
            results = vector_service.search_similar(
                chatbot_id=chatbot_id,
                query=query,
                limit=2
            )
            all_results.extend(results)
        
        if all_results:
            # Extract version information from results
            version_info = []
            for result in all_results[:3]:  # Top 3 results
                content = result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', '')
                version_info.append(content)
            
            return f"Version information found: {' | '.join(version_info)}"
        else:
            return f"No version information found for chatbot '{chatbot_id}'. Documentation may need to be ingested first."
            
    except Exception as e:
        logger.error(f"Error retrieving version information: {str(e)}")
        return f"Error retrieving version information: {str(e)}"


# Gemini tool declaration
GEMINI_TOOL_DECLARATION = {
    "name": "get_api_version_info",
    "description": "Get version information about the API from documentation database",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
