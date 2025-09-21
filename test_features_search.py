"""
Enhanced search function for finding specific feature information
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from agent_advanced import AdvancedMDSAgent

def main():
    """Test specific searches for the features table."""
    agent = AdvancedMDSAgent()
    
    # Search for the table chunk specifically
    search_results = agent.rag_processor.search_chunks(
        "New software features Ease of Use Feature Set Interoperability Security Fabric Congestion", 
        top_k=10
    )
    
    print("🔍 Search Results for New Software Features:")
    print("=" * 80)
    
    found_table = False
    for i, result in enumerate(search_results):
        if result['metadata'].get('chunk_type') == 'table' and 'New Software Features' in result['metadata'].get('table_title', ''):
            found_table = True
            print(f"✅ FOUND THE TABLE! (Result #{i+1})")
            print(f"   Similarity Score: {result['similarity_score']:.4f}")
            print(f"   Source: {result['metadata']['source_file']}")
            print(f"   Table Title: {result['metadata']['table_title']}")
            print(f"   Content Length: {len(result['content'])} chars")
            print("\\n📄 Table Content:")
            print("-" * 40)
            print(result['content'])
            print("=" * 80)
            break
    
    if not found_table:
        print("❌ Table chunk not found in top results")
        print("Top results were:")
        for i, result in enumerate(search_results[:3]):
            print(f"{i+1}. Score: {result['similarity_score']:.4f}")
            print(f"   Type: {result['metadata'].get('chunk_type', 'unknown')}")
            print(f"   Source: {result['metadata']['source_file']}")
            print(f"   Preview: {result['content'][:100]}...")
            print()

    # Now test with a more direct query using the table content
    if found_table:
        print("\\n🤖 Testing LLM Analysis with Table Content:")
        print("-" * 60)
        
        response = agent.ask_question(
            "What are the new features in NX-OS 9.4.4? List them by category: Ease of Use, Feature Set, Interoperability, and Security.",
            top_k=10,
            include_context=False
        )
        
        print(f"Question: {response['question']}")
        print(f"\\nAnswer: {response['answer']}")
        print(f"\\nSources: {response['sources']}")


if __name__ == "__main__":
    main()