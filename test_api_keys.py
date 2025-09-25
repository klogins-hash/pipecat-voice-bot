#!/usr/bin/env python3
"""
API Key Testing Script

This script tests your API keys to ensure they're working correctly
before running the full bot.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_cohere():
    """Test Cohere API key with a simple request."""
    try:
        import cohere
        
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            print("❌ COHERE_API_KEY not found in environment")
            return False
            
        print(f"🔑 Testing Cohere API key: {api_key[:20]}...")
        
        client = cohere.AsyncClientV2(api_key=api_key)
        
        # Test with a simple request
        response = await client.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "user", "content": "Hello, just testing the API. Please respond with 'API test successful'."}],
            max_tokens=50
        )
        
        print("✅ Cohere API key is working!")
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            if hasattr(response.message.content[0], 'text'):
                print(f"   Response: {response.message.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Cohere API key test failed: {e}")
        return False

async def test_cartesia():
    """Test Cartesia API key."""
    try:
        import cartesia
        
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            print("❌ CARTESIA_API_KEY not found in environment")
            return False
            
        print(f"🔑 Testing Cartesia API key: {api_key[:20]}...")
        
        client = cartesia.Cartesia(api_key=api_key)
        
        # Test by listing voices (simple API call)
        voices = client.voices.list()
        voice_list = list(voices)
        
        print("✅ Cartesia API key is working!")
        print(f"   Found {len(voice_list)} voices available")
        return True
        
    except Exception as e:
        print(f"❌ Cartesia API key test failed: {e}")
        return False

async def test_openai():
    """Test OpenAI API key with a simple request."""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
            
        print(f"🔑 Testing OpenAI API key: {api_key[:20]}...")
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        # Test with a simple request
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, just testing the API. Please respond with 'API test successful'."}],
            max_tokens=50
        )
        
        print("✅ OpenAI API key is working!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API key test failed: {e}")
        return False

async def main():
    """Run all API key tests."""
    print("🧪 Testing API Keys...")
    print("=" * 50)
    
    cartesia_ok = await test_cartesia()
    print()
    openai_ok = await test_openai()
    print()
    cohere_ok = await test_cohere()
    
    print()
    print("=" * 50)
    if cartesia_ok and openai_ok:
        print("🎉 Cartesia + OpenAI keys are working! Recommended bot:")
        print("\n🚀 Ready to run:")
        print("   uv run bot_cartesia_openai.py")
        
        if cohere_ok:
            print("\n🎯 Alternative (Cohere also working):")
            print("   uv run bot_cartesia_cohere_direct.py")
    elif cartesia_ok and cohere_ok:
        print("🎉 Cartesia + Cohere keys are working!")
        print("\n🚀 Ready to run:")
        print("   uv run bot_cartesia_cohere_direct.py")
    else:
        print("⚠️  Some API keys have issues. Please check and fix before running the bot.")
        
        if not cartesia_ok:
            print("\n🔧 Cartesia troubleshooting:")
            print("   1. Check your API key at https://play.cartesia.ai")
            print("   2. Make sure your account is active")
            print("   3. Verify the key is copied correctly (no extra spaces)")
            
        if not openai_ok:
            print("\n🔧 OpenAI troubleshooting:")
            print("   1. Check your API key at https://platform.openai.com/api-keys")
            print("   2. Make sure your account has credits")
            print("   3. Verify the key is copied correctly (no extra spaces)")
            
        if not cohere_ok:
            print("\n🔧 Cohere troubleshooting:")
            print("   1. Check your API key at https://dashboard.cohere.com/api-keys")
            print("   2. Make sure your account is active and has credits")
            print("   3. Verify the key is copied correctly (no extra spaces)")

if __name__ == "__main__":
    asyncio.run(main())
