#!/usr/bin/env python3
"""
Setup script for configuring OpenRouter.ai with Mistral free LLM.
"""

import os
import sys
from pathlib import Path

def setup_openrouter_mistral():
    """Guide user through OpenRouter setup for Mistral."""
    print("🚀 Setting up OpenRouter.ai with Mistral Small 3.2 24B")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        print("\n📋 Setup Steps:")
        print("1. 🌐 Go to https://openrouter.ai/")
        print("2. 📝 Sign up for a free account")  
        print("3. 🔑 Get your API key from the dashboard")
        print("4. ⚙️  Set the environment variable:")
        print("   export OPENROUTER_API_KEY='your_key_here'")
        print("\n🔧 Add this to your shell config:")
        print("   echo 'export OPENROUTER_API_KEY=\"your_key_here\"' >> ~/.zshrc")
        print("   source ~/.zshrc")
        
        # Offer to set it temporarily
        user_key = input("\n🔑 Paste your OpenRouter API key here (or press Enter to skip): ").strip()
        if user_key:
            os.environ['OPENROUTER_API_KEY'] = user_key
            print("✅ API key set temporarily for this session")
        else:
            print("⚠️  Please set OPENROUTER_API_KEY before running the agent")
            return False
    else:
        print("✅ OPENROUTER_API_KEY found in environment")
    
    # Test the connection with Mistral
    print("\n🧪 Testing Mistral connection...")
    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        
        # Simple test using the agent's LLM setup
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model="mistralai/mistral-small-3.2-24b-instruct:free",
            temperature=0.1,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": "https://github.com/jasonmooney/mds_knowledge_capture",
                    "X-Title": "MDS Knowledge Capture Agent"
                }
            }
        )
        
        # Test with a simple message
        from langchain_core.messages import HumanMessage
        
        test_message = HumanMessage(content="Hello! Please respond with 'Mistral connection successful' to confirm.")
        response = llm.invoke([test_message])
        
        if response and "successful" in response.content.lower():
            print("✅ Mistral connection successful!")
            print(f"📊 Model: mistralai/mistral-small-3.2-24b-instruct:free")
            print(f"🔗 Response: {response.content[:100]}...")
            return True
        else:
            print("❌ Connection test failed")
            print(f"Response: {response.content if response else 'None'}")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import required libraries: {e}")
        print("💡 Make sure you've installed requirements: pip install langchain-openai")
        return False
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        if "rate limit" in str(e).lower():
            print("💡 Rate limited - this is normal for free tier")
            print("⏳ Try again in a few minutes")
        elif "api_key" in str(e).lower():
            print("💡 API key issue - check your OpenRouter key")
        return False

def show_mistral_benefits():
    """Show why Mistral is good for MDS documentation."""
    print("\n🎯 Why Mistral Small 3.2 24B for MDS Knowledge Capture:")
    print("=" * 60)
    
    benefits = [
        "📊 24B parameters = Superior technical reasoning",
        "📄 Excellent JSON output consistency", 
        "🔧 Strong technical documentation understanding",
        "📚 128k context window handles full Cisco docs",
        "🆕 Recent release (Dec 2024) with improvements",
        "✅ Proven reliability in production environments",
        "💰 Completely FREE via OpenRouter",
        "⚡ Good performance for structured analysis"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print(f"\n🚀 Perfect for your scraper's needs:")
    print(f"   • Document categorization (Release Notes, Command Ref, etc.)")
    print(f"   • Version extraction from URLs and content")
    print(f"   • Hierarchical document relationship analysis")
    print(f"   • JSON metadata generation")

if __name__ == "__main__":
    print("🤖 MDS Knowledge Capture Agent - Mistral Setup")
    print("Configuring free Mistral Small 3.2 24B for technical documentation")
    print()
    
    success = setup_openrouter_mistral()
    
    if success:
        show_mistral_benefits()
        print("\n🎉 Setup complete! You can now run the MDS Agent with Mistral.")
        print("💡 Run: python src/agent.py")
    else:
        print("\n❌ Setup incomplete. Please resolve the issues above.")
        print("💡 Need help? Check https://openrouter.ai/docs")