#!/usr/bin/env python3
"""
Test the final fix for the RAG problem with NX-OS 9.4.4 features.
"""

import sys
sys.path.append('src')

from agent_advanced import AdvancedMDSAgent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("🔧 Testing FINAL FIX for NX-OS 9.4.4 features query...")
    print("=" * 70)
    
    # Initialize agent
    agent = AdvancedMDSAgent()
    
    # The original problematic query
    question = "What are the new features in NX-OS 9.4.4?"
    
    print(f"❓ Question: {question}")
    print("-" * 70)
    
    # Get response
    response = agent.ask_question(question)
    
    # Show the answer
    print("📝 ANSWER:")
    print(response['answer'])
    print()
    
    # Show sources
    print("📚 SOURCES:")
    for source in response['sources']:
        print(f"  - {source}")
    print()
    
    # Show search details
    if 'search_results' in response:
        print("🔍 SEARCH DETAILS:")
        for i, result in enumerate(response['search_results'][:3]):  # Show top 3
            metadata = result['metadata']
            content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            
            print(f"\n  Result {i+1}:")
            print(f"    Type: {metadata.get('chunk_type', 'text')}")
            print(f"    Table Title: {metadata.get('table_title', 'N/A')}")
            print(f"    Similarity: {result['similarity_score']:.4f}")
            print(f"    Content: {content_preview}")
    
    print("\n" + "=" * 70)
    print("🎯 KEY SUCCESS METRICS:")
    
    # Check if key features are mentioned
    answer_lower = response['answer'].lower()
    key_features = [
        'fabric congestion',
        'diagnostics',
        'sma',
        'fpin',
        'rfc 5424',
        'aes-256'
    ]
    
    found_features = [f for f in key_features if f in answer_lower]
    
    print(f"✅ Key features found: {len(found_features)}/{len(key_features)}")
    for feature in found_features:
        print(f"  ✓ {feature.upper()}")
    
    for feature in key_features:
        if feature not in found_features:
            print(f"  ❌ {feature.upper()} (missing)")
    
    # Check for table content
    table_indicators = ['ease of use', 'feature set', 'interoperability', 'security']
    found_indicators = [ind for ind in table_indicators if ind in answer_lower]
    
    print(f"\n✅ Table structure indicators: {len(found_indicators)}/{len(table_indicators)}")
    for indicator in found_indicators:
        print(f"  ✓ {indicator.title()}")
    
    # Success assessment
    success_score = (len(found_features) / len(key_features)) * 0.7 + (len(found_indicators) / len(table_indicators)) * 0.3
    
    print(f"\n🏆 OVERALL SUCCESS SCORE: {success_score:.2%}")
    
    if success_score > 0.8:
        print("🎉 EXCELLENT! Problem is FIXED!")
    elif success_score > 0.6:
        print("👍 GOOD progress, minor improvements needed")
    else:
        print("⚠️  Still needs work")

if __name__ == "__main__":
    main()