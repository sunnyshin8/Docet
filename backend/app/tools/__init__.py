
import importlib
import inspect
from typing import List, Dict, Any, Callable, Set
import logging

logger = logging.getLogger(__name__)

_tool_functions = {}
_tool_declarations = {}
_chatbot_tool_access = {}

def register_tool(func: Callable, declaration: Dict[str, Any]):
    _tool_functions[declaration["name"]] = func
    _tool_declarations[declaration["name"]] = declaration
    logger.info(f"Registered tool: {declaration['name']}")

def get_all_tool_functions() -> Dict[str, Callable]:
    return _tool_functions.copy()

def get_all_tool_declarations() -> List[Dict[str, Any]]:
    return list(_tool_declarations.values())

def get_chatbot_tool_declarations(chatbot_id: str) -> List[Dict[str, Any]]:
    if chatbot_id not in _chatbot_tool_access:
        return get_all_tool_declarations()
    
    allowed_tools = _chatbot_tool_access[chatbot_id]
    return [decl for name, decl in _tool_declarations.items() if name in allowed_tools]

def get_tool_function(name: str) -> Callable:
    return _tool_functions.get(name)

def is_tool_allowed_for_chatbot(tool_name: str, chatbot_id: str) -> bool:
    if chatbot_id not in _chatbot_tool_access:
        return tool_name in _tool_functions
    
    return tool_name in _chatbot_tool_access[chatbot_id]

def set_chatbot_tools(chatbot_id: str, tool_names: List[str]):
    valid_tools = set(tool_names) & set(_tool_functions.keys())
    _chatbot_tool_access[chatbot_id] = valid_tools
    logger.info(f"Set tools for chatbot {chatbot_id}: {list(valid_tools)}")

def enable_tool_for_chatbot(chatbot_id: str, tool_name: str):
    if tool_name not in _tool_functions:
        logger.warning(f"Tool {tool_name} not found")
        return False
    
    if chatbot_id not in _chatbot_tool_access:
        _chatbot_tool_access[chatbot_id] = set(_tool_functions.keys())
    
    _chatbot_tool_access[chatbot_id].add(tool_name)
    logger.info(f"Enabled tool {tool_name} for chatbot {chatbot_id}")
    return True

def disable_tool_for_chatbot(chatbot_id: str, tool_name: str):
    if chatbot_id not in _chatbot_tool_access:
        _chatbot_tool_access[chatbot_id] = set(_tool_functions.keys())
    
    _chatbot_tool_access[chatbot_id].discard(tool_name)
    logger.info(f"Disabled tool {tool_name} for chatbot {chatbot_id}")

def get_chatbot_tool_status() -> Dict[str, List[str]]:
    status = {}
    for chatbot_id, tools in _chatbot_tool_access.items():
        status[chatbot_id] = list(tools)
    return status

def _discover_tools():
    tool_modules = [
        'version_tool',
        'rag_tool'
    ]
    
    for module_name in tool_modules:
        try:
            module = importlib.import_module(f'.{module_name}', package=__name__)
            
            if hasattr(module, 'GEMINI_TOOL_DECLARATION'):
                declaration = module.GEMINI_TOOL_DECLARATION
                func_name = declaration["name"]
                
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    register_tool(func, declaration)
                else:
                    logger.warning(f"Tool function '{func_name}' not found in {module_name}")
            else:
                logger.warning(f"GEMINI_TOOL_DECLARATION not found in {module_name}")
                
        except ImportError as e:
            logger.error(f"Failed to import tool module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error discovering tools in {module_name}: {e}")

_discover_tools()

__all__ = list(_tool_functions.keys()) + [
    "get_all_tool_functions",
    "get_all_tool_declarations", 
    "get_chatbot_tool_declarations",
    "get_tool_function",
    "register_tool",
    "is_tool_allowed_for_chatbot",
    "set_chatbot_tools",
    "enable_tool_for_chatbot", 
    "disable_tool_for_chatbot",
    "get_chatbot_tool_status"
]
