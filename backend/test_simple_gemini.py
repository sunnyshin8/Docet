
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from app.llm.gemini_service import get_gemini_llm_service

async def test_simple_gemini():
    
    print("🧪 Testing Simple Gemini Response")
    print("=" * 40)
    
    service = get_gemini_llm_service()
    
    test_prompts = [
        "Hello! How are you?",
        "What is an API?",
        "Explain REST in one sentence."
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt}")
        print("-" * 30)
        
        try:
            response = await service.generate_response(prompt, temperature=0.7)
            print(f"✅ Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Simple test complete!")

if __name__ == "__main__":
    asyncio.run(test_simple_gemini())