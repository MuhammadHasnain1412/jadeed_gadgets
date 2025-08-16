#!/usr/bin/env python3
"""
Test script to verify JadeedBot chatbot functionality.
Run this script to test the chatbot without starting the full Django server.
"""

import sys
import os
import django
from django.conf import settings

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from chatbot.views import GROQ_API_KEY, SYSTEM_PROMPT

def test_setup():
    """Test the basic setup of the chatbot."""
    print("=== JadeedBot Setup Test ===")
    
    # Test 1: Check if API key is configured
    print("\n1. Testing API Key Configuration:")
    if GROQ_API_KEY and GROQ_API_KEY != "your-groq-api-key-here":
        print("   ✅ API key is configured")
    else:
        print("   ❌ API key not configured")
        print("   📝 Please run: python setup_groq_api.py")
        return False
    
    # Test 2: Check if httpx is installed
    print("\n2. Testing httpx dependency:")
    try:
        import httpx
        print("   ✅ httpx is installed")
    except ImportError:
        print("   ❌ httpx not installed")
        print("   📝 Please run: pip install httpx")
        return False
    
    # Test 3: Check Django app configuration
    print("\n3. Testing Django app configuration:")
    if 'chatbot' in settings.INSTALLED_APPS:
        print("   ✅ chatbot app is in INSTALLED_APPS")
    else:
        print("   ❌ chatbot app not in INSTALLED_APPS")
        return False
    
    # Test 4: Check system prompt
    print("\n4. Testing JadeedBot system prompt:")
    if "JadeedBot" in SYSTEM_PROMPT and "Assalamualaikum" in SYSTEM_PROMPT:
        print("   ✅ System prompt is configured correctly")
    else:
        print("   ❌ System prompt needs configuration")
        return False
    
    # Test 5: Check template files
    print("\n5. Testing template files:")
    chatbox_template = os.path.join("templates", "chatbot", "chatbox.html")
    if os.path.exists(chatbox_template):
        print("   ✅ Chatbox template exists")
    else:
        print("   ❌ Chatbox template missing")
        return False
    
    return True

def test_api_connection():
    """Test connection to Groq API (requires valid API key)."""
    print("\n=== API Connection Test ===")
    
    if GROQ_API_KEY == "your-groq-api-key-here":
        print("❌ Cannot test API connection - API key not configured")
        return False
    
    try:
        import httpx
        from chatbot.views import GROQ_API_URL, GROQ_MODEL
        
        # Test API connection
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 10
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(GROQ_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                print("✅ API connection successful")
                return True
            else:
                print(f"❌ API connection failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def main():
    """Run all tests."""
    print("🤖 JadeedBot Testing Suite")
    print("=" * 50)
    
    # Run setup tests
    if not test_setup():
        print("\n❌ Setup test failed!")
        return False
    
    # Run API connection test
    api_test_passed = test_api_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("✅ Setup: PASSED")
    print(f"{'✅' if api_test_passed else '❌'} API Connection: {'PASSED' if api_test_passed else 'FAILED'}")
    
    if api_test_passed:
        print("\n🎉 All tests passed! Your chatbot is ready to use.")
        print("📝 Next steps:")
        print("   1. Run: python manage.py runserver")
        print("   2. Visit: http://localhost:8000")
        print("   3. Click the chat button in the bottom right corner")
        print("   4. Start chatting with JadeedBot!")
        return True
    else:
        print("\n⚠️  Setup is complete but API connection failed.")
        print("📝 Please check your API key and internet connection.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
