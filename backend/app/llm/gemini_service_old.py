"""Gemini LLM service for cloud-based language model inference."""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
import google.genai as genai
from google.genai import types

from ..config import settings

logger = logging.getLogger(__name__)


def get_api_version_info(chatbot_id: str = "default") -> str:
    """
    Get API version information from the documentation database.
    
    Args:
        chatbot_id: The chatbot identifier to search for version info
        
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
        return f"Error retrieving version information: {str(e)}"


def calculate_simple_math(expression: str) -> str:
    """
    Calculate simple mathematical expressions safely.
    
    Args:
        expression: A simple math expression like "2+3" or "10*5"
        
    Returns:
        String result of the calculation or error message
    """
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return f"Invalid expression: '{expression}'. Only basic math operations (+, -, *, /, parentheses) and numbers are allowed."
        
        # Evaluate safely
        result = eval(expression)
        return f"The result of {expression} is {result}"
        
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


class GeminiLLMService:
    """Service for Gemini 2.5 Flash language model."""
    
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """Initialize the Gemini LLM service."""
        self.model_name = model_name
        self.model = None
        self.api_key = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Gemini client with API key."""
        try:
            # Get API key from environment
            self.api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
            if not self.api_key:
                logger.warning("GOOGLE_AI_STUDIO_API_KEY not found in environment variables")
                return
            
            # Initialize client with new SDK
            self.client = genai.Client(api_key=self.api_key)
            
            # Define native tools
            self.tools = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name="get_api_version_info",
                            description="Get version information about the API from documentation database",
                            parameters=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "chatbot_id": types.Schema(
                                        type=types.Type.STRING,
                                        description="The chatbot identifier to search for version info"
                                    )
                                },
                                required=["chatbot_id"]
                            )
                        ),
                        types.FunctionDeclaration(
                            name="calculate_simple_math",
                            description="Calculate simple mathematical expressions safely",
                            parameters=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "expression": types.Schema(
                                        type=types.Type.STRING,
                                        description="A simple math expression like '2+3' or '10*5'"
                                    )
                                },
                                required=["expression"]
                            )
                        )
                    ]
                )
            ]
            
            logger.info(f"Gemini {self.model_name} initialized successfully with google-genai SDK!")
            
        except Exception as e:
            logger.error(f"Failed to setup Gemini client: {e}")
            raise
    
    async def generate_response(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_output_tokens: int = 2048  # Keep parameter for API compatibility
    ) -> Union[str, Dict[str, Any]]:
        """Generate response using Gemini."""
        
        if not self.client:
            raise Exception("Gemini client not initialized. Please set GOOGLE_AI_STUDIO_API_KEY environment variable.")
        
        try:
            # Use default generation settings for best compatibility
            # Only add custom config if needed for specific use cases
            if temperature != 0.7 or max_output_tokens != 2048:
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    candidate_count=1
                )
                response = self.model.generate_content(prompt, generation_config=generation_config)
            else:
                # Use default settings for best results
                response = self.model.generate_content(prompt)
            
            # Handle tool calls
            if response.candidates and response.candidates[0].content:
                candidate = response.candidates[0]
                
                # Check if Gemini wants to use tools
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Execute the function call
                            function_name = part.function_call.name
                            function_args = dict(part.function_call.args)
                            
                            logger.info(f"Gemini calling function: {function_name} with args: {function_args}")
                            
                            # Execute the function
                            if function_name == "get_api_version_info":
                                result = get_api_version_info(**function_args)
                            elif function_name == "calculate_simple_math":
                                result = calculate_simple_math(**function_args)
                            else:
                                result = f"Unknown function: {function_name}"
                            
                            # Create function response and continue conversation
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result}
                                )
                            )
                            
                            # Continue conversation with function result
                            messages = [
                                {"role": "user", "parts": [prompt]},
                                {"role": "model", "parts": response.candidates[0].content.parts},
                                {"role": "tool", "parts": [function_response]}
                            ]
                            
                            final_response = self.model.generate_content(messages)
                            
                            if final_response.candidates and final_response.candidates[0].content:
                                return final_response.candidates[0].content.parts[0].text.strip()
                            else:
                                return f"Function executed: {result}"
            
            # Remove debug logging for production use
            # logger.warning("Raw response: %s", response)

            # Check if response has content
            if not response.candidates:
                logger.warning("No candidates in Gemini response")
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
            candidate = response.candidates[0]
            
            # Check for finish reason
            if hasattr(candidate, 'finish_reason'):
                if candidate.finish_reason.name == 'MAX_TOKENS':
                    logger.warning("Response truncated due to max tokens limit")
                elif candidate.finish_reason.name in ['SAFETY', 'RECITATION']:
                    logger.warning(f"Response blocked due to: {candidate.finish_reason.name}")
                    return "I apologize, but I cannot provide a response to this query due to content policies. Please try rephrasing your question."
            
            if not candidate.content or not candidate.content.parts:
                logger.warning("Empty content or parts in Gemini response")
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
            response_text = candidate.content.parts[0].text
            
            # Check if response is a JSON action request
            try:
                # Look for JSON in the response
                if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                    return json.loads(response_text.strip())
            except json.JSONDecodeError:
                pass
            
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate response with Gemini: {str(e)}")
            return "I apologize, but I'm unable to generate a response at the moment. Please try again."
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": "Google AI Studio",
            "model_type": "Gemini 2.5 Flash",
            "context_window": "1M tokens",
            "api_key_configured": bool(self.api_key),
            "model_initialized": bool(self.model)
        }


# Global instance
gemini_llm_service = GeminiLLMService()

def get_gemini_llm_service() -> GeminiLLMService:
    """Get the global Gemini LLM service instance."""
    return gemini_llm_service
