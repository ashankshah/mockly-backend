"""
Test script for Mistral-7B-Instruct-v0.2 implementation
Run this to test your content scoring and STAR analysis
"""

import asyncio
import os
from dotenv import load_dotenv
from app.scoring import evaluate_content_quality, analyze_star_structure

load_dotenv()

async def test_mistral_implementation():
    print("🧪 Testing Mistral-7B-Instruct-v0.2 Implementation")
    print("=" * 50)
    
    # Test interview response
    test_transcript = """
    I was working as a software engineer at a startup when we faced a critical bug in our payment system. 
    The issue was causing customers to be charged twice for their purchases. My task was to identify and fix 
    this bug within 24 hours to prevent further financial losses. I immediately started by analyzing the 
    payment processing code and found that there was a race condition in our database transactions. 
    I implemented a solution using database locks and added proper error handling. As a result, we 
    successfully fixed the bug within 18 hours, prevented any additional double charges, and improved 
    our overall payment system reliability.
    """
    
    print("📝 Test Transcript:")
    print(test_transcript.strip())
    print("\n" + "=" * 50)
    
    # Test content evaluation
    print("🎯 Testing Content Evaluation...")
    try:
        content_score, content_tips = await evaluate_content_quality(test_transcript)
        print(f"✅ Content Score: {content_score}/5")
        print(f"✅ Content Tips: {content_tips}")
    except Exception as e:
        print(f"❌ Content Evaluation Error: {e}")
    
    print("\n" + "=" * 50)
    
    # Test STAR analysis
    print("⭐ Testing STAR Analysis...")
    try:
        star_result = await analyze_star_structure(test_transcript)
        print("✅ STAR Analysis Results:")
        print(f"   Situation: {star_result['situation']}")
        print(f"   Task: {star_result['task']}")
        print(f"   Action: {star_result['action']}")
        print(f"   Result: {star_result['result']}")
    except Exception as e:
        print(f"❌ STAR Analysis Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete!")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found in environment variables")
        print("Please set your OpenRouter API key in a .env file")
        exit(1)
    
    asyncio.run(test_mistral_implementation()) 