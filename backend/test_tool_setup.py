
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from app.llm.gemini_service import get_gemini_llm_service

async def test_tool_setup():
    
    print("🔧 Testing Gemini Tool Configuration")
    print("=" * 50)
    
    service = get_gemini_llm_service()
    
    if service.model:
        print(f"✅ Model initialized: {service.model._model_name}")
        
        try:
            if hasattr(service.model, '_tools') and service.model._tools:
                print(f"✅ Model has tools configured")
                print(f"   Tools object: {type(service.model._tools)}")
                if hasattr(service.model._tools, 'to_proto'):
                    print(f"   Tools proto available")
            else:
                print("❌ No tools found in model configuration")
        except Exception as e:
            print(f"⚠️  Error inspecting tools: {e}")
    else:
        print("❌ Model not initialized")
    
    explicit_prompts = [
        "Please use the calculate_simple_math function to compute 5 + 3",
        "I need you to call the get_api_version_info function with chatbot_id 'petstore-bot'",
        "Use available tools to calculate 10 * 5",
    ]
    
    for i, prompt in enumerate(explicit_prompts, 1):
        print(f"\n📝 Explicit Test {i}:")
        print(f"Prompt: {prompt}")
        print("-" * 40)
        
        try:
            response = await service.generate_response(prompt)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Tool configuration test complete!")

if __name__ == "__main__":
    asyncio.run(test_tool_setup())