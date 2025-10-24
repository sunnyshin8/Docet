
import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
import google.genai as genai

from ..config import settings
from ..tools import get_all_tool_functions, get_all_tool_declarations, get_chatbot_tool_declarations, get_tool_function, is_tool_allowed_for_chatbot

logger = logging.getLogger(__name__)


class GeminiLLMService:
    
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.model_name = model_name
        self.client = None
        self.api_key = None
        self.tools = []
        self.conversation_history = {}
        self._setup_client()
    
    def _setup_client(self):
        try:
            self.api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
            if not self.api_key:
                logger.warning("GOOGLE_AI_STUDIO_API_KEY not found in environment variables")
                return
            
            self.client = genai.Client(api_key=self.api_key)
            
            logger.info(f"Gemini {self.model_name} initialized successfully with dynamic tool loading!")
            
        except Exception as e:
            logger.error(f"Failed to setup Gemini client: {e}")
            raise
    
    def _get_tools_for_chatbot(self, chatbot_id: str) -> List[genai.types.Tool]:
        tool_declarations = get_chatbot_tool_declarations(chatbot_id)
        
        if tool_declarations:
            function_declarations = []
            for tool_decl in tool_declarations:
                function_declarations.append(
                    genai.types.FunctionDeclaration(
                        name=tool_decl["name"],
                        description=tool_decl["description"],
                        parameters=tool_decl["parameters"]
                    )
                )
            
            return [genai.types.Tool(function_declarations=function_declarations)]
        else:
            return []
    
    def _get_conversation_history(self, session_id: str) -> List[genai.types.Content]:
        return self.conversation_history.get(session_id, [])
    
    def _add_to_conversation_history(self, session_id: str, content: genai.types.Content):
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append(content)
        
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
    
    async def generate_response(
        self, 
        prompt: str, 
        chatbot_id: str = "default",
        session_id: str = "default",
        temperature: float = 0.7,
        max_output_tokens: int = 2048
        , return_function_call: bool = False
    ) -> Union[str, Dict[str, Any]]:
        
        if not self.client:
            raise Exception("Gemini client not initialized. Please set GOOGLE_AI_STUDIO_API_KEY environment variable.")
        
        try:
            current_message = genai.types.Content(parts=[genai.types.Part(text=prompt)])
            
            conversation_history = self._get_conversation_history(session_id)
            
            conversation_contents = conversation_history + [current_message]
            
            chatbot_tools = self._get_tools_for_chatbot(chatbot_id)
            
            logger.info(f"Generating response for session {session_id} with {len(conversation_history)} previous messages and {len(chatbot_tools[0].function_declarations) if chatbot_tools else 0} tools")
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=conversation_contents,
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    tools=chatbot_tools
                )
            )
            
            self._add_to_conversation_history(session_id, current_message)
            
            if response.candidates and response.candidates[0].content:
                candidate = response.candidates[0]
                
                for part in candidate.content.parts:
                    if part.function_call:
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args) if part.function_call.args else {}
                        
                        logger.info(f"Gemini requested function call: {function_name} with args: {function_args}")

                        if return_function_call:
                            return {
                                "action": "function_call",
                                "function_name": function_name,
                                "function_args": function_args
                            }

                        if not is_tool_allowed_for_chatbot(function_name, chatbot_id):
                            result = f"Tool '{function_name}' is not available for chatbot '{chatbot_id}'"
                        else:
                            tool_function = get_tool_function(function_name)
                            if tool_function:
                                func_signature = tool_function.__code__.co_varnames
                                if 'chatbot_id' in func_signature:
                                    function_args["chatbot_id"] = chatbot_id

                                result = tool_function(**function_args)
                            else:
                                result = f"Unknown function: {function_name}"

                        function_response = genai.types.Content(
                            parts=[
                                genai.types.Part(
                                    function_response=genai.types.FunctionResponse(
                                        name=function_name,
                                        response={"result": result}
                                    )
                                )
                            ]
                        )

                        self._add_to_conversation_history(session_id, candidate.content)
                        self._add_to_conversation_history(session_id, function_response)

                        final_response = await self.client.aio.models.generate_content(
                            model=self.model_name,
                            contents=self._get_conversation_history(session_id),
                            config=genai.types.GenerateContentConfig(
                                temperature=temperature,
                                max_output_tokens=max_output_tokens,
                                tools=chatbot_tools
                            )
                        )

                        if (final_response.candidates and 
                            final_response.candidates[0].content and 
                            final_response.candidates[0].content.parts):
                            final_text = final_response.candidates[0].content.parts[0].text.strip()
                            self._add_to_conversation_history(
                                session_id, 
                                genai.types.Content(parts=[genai.types.Part(text=final_text)])
                            )
                            return final_text
                        else:
                            return f"Function executed: {result}"
                
                if candidate.content.parts and candidate.content.parts[0].text:
                    response_text = candidate.content.parts[0].text.strip()
                    self._add_to_conversation_history(
                        session_id,
                        genai.types.Content(parts=[genai.types.Part(text=response_text)])
                    )
                    return response_text
            
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
        except Exception as e:
            logger.error(f"Failed to generate response with Gemini: {str(e)}")
            return "I apologize, but I'm unable to generate a response at the moment. Please try again."
    
    async def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": "Google AI Studio",
            "model_type": "Gemini 2.5 Pro",
            "context_window": "1M tokens",
            "api_key_configured": bool(self.api_key),
            "client_initialized": bool(self.client),
            "total_tools": len(get_all_tool_declarations()),
            "available_tools": [decl["name"] for decl in get_all_tool_declarations()],
            "active_sessions": len(self.conversation_history),
            "tool_management": "per-chatbot",
            "sdk": "google-genai"
        }
    
    def get_chatbot_tools_info(self, chatbot_id: str) -> Dict[str, Any]:
        chatbot_tools = get_chatbot_tool_declarations(chatbot_id)
        return {
            "chatbot_id": chatbot_id,
            "tools_count": len(chatbot_tools),
            "available_tools": [tool["name"] for tool in chatbot_tools],
            "tool_details": chatbot_tools
        }
    
    def clear_session_history(self, session_id: str) -> bool:
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared conversation history for session: {session_id}")
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        history = self.conversation_history.get(session_id, [])
        return {
            "session_id": session_id,
            "message_count": len(history),
            "last_activity": "recent" if history else "none"
        }


gemini_llm_service = GeminiLLMService()

def get_gemini_llm_service() -> GeminiLLMService:
    return gemini_llm_service