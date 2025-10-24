"""Chat API endpoints for RAG-powered conversations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from ..chat.service import ChatService
from ..rag.service import get_rag_service
from ..tools import set_chatbot_tools, enable_tool_for_chatbot, disable_tool_for_chatbot, get_chatbot_tool_status, get_chatbot_tool_declarations

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # user, assistant, system
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    chatbot_id: str  # Required: which chatbot to chat with
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    session_id: str
    sources: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    """Chat session model."""
    session_id: str
    created_at: str
    messages: List[ChatMessage]
    metadata: Optional[Dict[str, Any]] = None


# In-memory session storage (replace with proper storage later)
session_storage: Dict[str, ChatSession] = {}


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response based on ingested documentation.
    
    Uses RAG (Retrieval-Augmented Generation) to provide contextual responses
    based on the documentation that has been ingested for the specific chatbot.
    """
    try:
        # Validate chatbot_id
        if not request.chatbot_id or len(request.chatbot_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="chatbot_id is required")
        
        # Get or create session (include chatbot_id in session key for isolation)
        session_key = f"{request.chatbot_id}:{request.session_id}" if request.session_id else f"{request.chatbot_id}:{_generate_session_id()}"
        
        if session_key not in session_storage:
            session_storage[session_key] = ChatSession(
                session_id=session_key,
                created_at=_get_current_timestamp(),
                messages=[],
                metadata={"chatbot_id": request.chatbot_id}
            )
        
        session = session_storage[session_key]
        
        # Add user message to session
        user_message = ChatMessage(
            role="user",
            content=request.message,
            metadata=request.context
        )
        session.messages.append(user_message)
        
        # Use RAG service to generate response
        rag_service = get_rag_service()
        rag_response = await rag_service.generate_response(
            chatbot_id=request.chatbot_id,
            query=request.message,
            session_id=session_key
        )
        
        # Add assistant message to session
        assistant_message = ChatMessage(
            role="assistant",
            content=rag_response["response"],
            metadata={
                "sources": rag_response.get("sources", []),
                "context_used": rag_response.get("context_used", False),
                "context_chunks_count": rag_response.get("context_chunks_count", 0)
            }
        )
        session.messages.append(assistant_message)
        
        return ChatResponse(
            message=rag_response["response"],
            session_id=session_key,
            sources=rag_response.get("sources", []),
            metadata={
                "chatbot_id": request.chatbot_id,
                "context_used": rag_response.get("context_used", False),
                "context_chunks_count": rag_response.get("context_chunks_count", 0)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_chat_sessions(chatbot_id: Optional[str] = None):
    """List all chat sessions, optionally filtered by chatbot."""
    sessions = []
    
    for session in session_storage.values():
        # Filter by chatbot_id if provided
        if chatbot_id:
            session_chatbot_id = session.metadata.get("chatbot_id") if session.metadata else None
            if session_chatbot_id != chatbot_id:
                continue
        
        sessions.append({
            "session_id": session.session_id,
            "created_at": session.created_at,
            "message_count": len(session.messages),
            "chatbot_id": session.metadata.get("chatbot_id") if session.metadata else None
        })
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get a specific chat session."""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_storage[session_id]


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session."""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del session_storage[session_id]
    return {"message": "Session deleted successfully"}


@router.post("/sessions/{session_id}/clear")
async def clear_chat_session(session_id: str):
    """Clear messages from a chat session."""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_storage[session_id].messages = []
    return {"message": "Session cleared successfully"}


@router.get("/chatbots/{chatbot_id}/info")
async def get_chatbot_info(chatbot_id: str):
    """Get information about a chatbot including knowledge stats."""
    try:
        rag_service = get_rag_service()
        stats = await rag_service.get_chatbot_knowledge_stats(chatbot_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbots/{chatbot_id}/tools")
async def get_chatbot_tools(chatbot_id: str):
    """Get available tools for a specific chatbot."""
    try:
        tools = get_chatbot_tool_declarations(chatbot_id)
        return {
            "chatbot_id": chatbot_id,
            "tools_count": len(tools),
            "tools": tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbots/{chatbot_id}/tools")
async def set_chatbot_tools_endpoint(chatbot_id: str, tool_names: List[str]):
    """Set which tools are available for a specific chatbot."""
    try:
        set_chatbot_tools(chatbot_id, tool_names)
        return {
            "message": f"Tools updated for chatbot {chatbot_id}",
            "chatbot_id": chatbot_id,
            "tools": tool_names
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbots/{chatbot_id}/tools/{tool_name}/enable")
async def enable_chatbot_tool(chatbot_id: str, tool_name: str):
    """Enable a specific tool for a chatbot."""
    try:
        success = enable_tool_for_chatbot(chatbot_id, tool_name)
        if success:
            return {
                "message": f"Tool {tool_name} enabled for chatbot {chatbot_id}",
                "chatbot_id": chatbot_id,
                "tool_name": tool_name,
                "enabled": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbots/{chatbot_id}/tools/{tool_name}/disable")
async def disable_chatbot_tool(chatbot_id: str, tool_name: str):
    """Disable a specific tool for a chatbot."""
    try:
        disable_tool_for_chatbot(chatbot_id, tool_name)
        return {
            "message": f"Tool {tool_name} disabled for chatbot {chatbot_id}",
            "chatbot_id": chatbot_id,
            "tool_name": tool_name,
            "enabled": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/status")
async def get_all_chatbot_tools_status():
    """Get tool access status for all chatbots."""
    try:
        status = get_chatbot_tool_status()
        return {
            "tool_status": status,
            "chatbot_count": len(status)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_session_id() -> str:
    """Generate a unique session ID."""
    import uuid
    return str(uuid.uuid4())


def _get_current_timestamp() -> str:
    """Get current timestamp as ISO string."""
    from datetime import datetime
    return datetime.utcnow().isoformat()