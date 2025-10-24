
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def detailed_info(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def execute(self, chatbot_id: str, **kwargs) -> Dict[str, Any]:
        pass
    
    def get_info_summary(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description
        }


class ToolRegistry:
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._chatbot_tool_configs: Dict[str, List[str]] = {}
    
    def register_tool(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        return self._tools.get(tool_name)
    
    def get_available_tools(self, chatbot_id: str = None) -> List[Dict[str, str]]:
        if chatbot_id and chatbot_id in self._chatbot_tool_configs:
            allowed_tools = self._chatbot_tool_configs[chatbot_id]
            return [self._tools[tool_name].get_info_summary() 
                    for tool_name in allowed_tools 
                    if tool_name in self._tools]
        else:
            return [tool.get_info_summary() for tool in self._tools.values()]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        tool = self.get_tool(tool_name)
        if tool:
            return tool.detailed_info
        return None
    
    def configure_chatbot_tools(self, chatbot_id: str, tool_names: List[str]):
        self._chatbot_tool_configs[chatbot_id] = tool_names
        logger.info(f"Configured tools for {chatbot_id}: {tool_names}")
    
    async def execute_tool(self, tool_name: str, chatbot_id: str, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": self.get_available_tools(chatbot_id)
            }
        
        try:
            return await tool.execute(chatbot_id, **kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "error": f"Failed to execute tool '{tool_name}': {str(e)}"
            }
