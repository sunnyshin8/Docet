
import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from app.rag.service import get_rag_service
from app.tools import tool_registry

async def test_gemini_rag():
    
    print("🧪 Testing Gemini RAG System")
    print("=" * 50)
    
    api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        print("❌ GOOGLE_AI_STUDIO_API_KEY not found in environment variables")
        print("   Please set your Google AI Studio API key:")
        print("   export GOOGLE_AI_STUDIO_API_KEY='your_api_key_here'")
        return
    
    print(f"✅ API key configured (ending with: ...{api_key[-8:]})")
    
    rag_service = get_rag_service()
    
    print("\n🔧 Available Tools:")
    available_tools = tool_registry.get_available_tools()
    for tool in available_tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    test_queries = [
        "What is 5 + 3?",  # Basic test
        "What version of the API is supported?",  # Tool usage test
        "How do I authenticate with this API?",  # Context retrieval test
        "Tell me about the rate limits"  # More context request test
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        try:
            chatbot_id = "petstore-bot"
            
            response = await rag_service.generate_response(
                chatbot_id=chatbot_id,
                query=query,
                session_id=f"test-session-{i}"
            )
            
            print(f"Response: {response['response']}")
            print(f"Context used: {response.get('context_used', False)}")
            print(f"Sources: {len(response.get('sources', []))}")
            
            if 'tool_used' in response:
                print(f"Tool used: {response['tool_used']}")
            
            if 'action_attempted' in response:
                print(f"Action attempted: {response['action_attempted']}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🔍 Testing Tool Info Retrieval:")
    print("-" * 40)
    
    tool_info = tool_registry.get_tool_info("version_info")
    if tool_info:
        print(f"Tool info retrieved successfully")
        print(f"Purpose: {tool_info.get('purpose', 'N/A')}")
    else:
        print("❌ Failed to retrieve tool info")
    
    print("\n✅ Testing complete!")
    print("\nNote: For full functionality, make sure to:")
    print("1. Ingest some API documentation using the ingestion endpoints")
    print("2. Set up your Google AI Studio API key")
    print("3. Configure chatbot-specific tools if needed")

if __name__ == "__main__":
    asyncio.run(test_gemini_rag())
