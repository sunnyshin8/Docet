
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from app.llm.gemini_service import get_gemini_llm_service

async def test_gemini_native_tools():
    
    print("🔧 Testing Gemini Native Tools")
    print("=" * 50)
    
    service = get_gemini_llm_service()
    
    test_cases = [
        {
            "query": "What is 5 + 3?",
            "expected_tool": "calculate_simple_math",
            "description": "Math calculation tool"
        },
        {
            "query": "What is 15 * 7?", 
            "expected_tool": "calculate_simple_math",
            "description": "Math multiplication tool"
        },
        {
            "query": "What version of the API is supported?",
            "expected_tool": "get_api_version_info", 
            "description": "API version info tool"
        },
        {
            "query": "Tell me about the API versions available",
            "expected_tool": "get_api_version_info",
            "description": "API version inquiry"
        },
        {
            "query": "Hello, how are you?",
            "expected_tool": None,
            "description": "Regular conversation (no tools)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"Expected tool: {test_case['expected_tool'] or 'None'}")
        print("-" * 40)
        
        try:
            response = await service.generate_response(test_case['query'])
            print(f"✅ Response: {response}")
            
            if isinstance(response, str) and "Function executed:" in response:
                print("🔧 Tool was executed!")
            elif test_case['expected_tool']:
                print("🤔 Expected tool usage but got regular response")
            else:
                print("💬 Regular conversation response")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Native tool testing complete!")
    print("\nNote: If tools are working, you should see function execution messages in the responses.")

if __name__ == "__main__":
    asyncio.run(test_gemini_native_tools())