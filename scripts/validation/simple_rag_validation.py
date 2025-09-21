#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Simple RAG Validation ===")
print("Shows actual retrieved content for manual evaluation")
print()

def run_simple_rag_validation():
    """Run RAG validation showing actual retrieved content."""
    
    try:
        processor = RAGDocumentProcessor()
        
        if not processor.vector_store or not processor.embeddings:
            print("❌ Vector store or embeddings not available")
            return
        
        # Use the test collection
        collection = processor.vector_store.get_or_create_collection("mds_test")
        count = collection.count()
        
        print(f"✅ Using collection 'mds_test' with {count} documents")
        
        if count == 0:
            print("❌ Test collection is empty")
            return
        
        # Test questions
        test_questions = [
            "What are the recommended software releases for Cisco MDS 9000 switches?",
            "How do I configure FCoE on MDS switches?",
            "What show commands are available for monitoring MDS switch status?",
        ]
        
        print(f"\n🧪 Testing RAG retrieval with {len(test_questions)} questions")
        print("=" * 80)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nTest {i}/{len(test_questions)}")
            print(f"Question: {question}")
            print("-" * 60)
            
            # Retrieve relevant documents
            query_embedding = processor.embeddings.embed_query(question)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=2,
                include=["documents", "distances", "metadatas"]
            )
            
            if results and results["documents"] and results["documents"][0]:
                retrieved_texts = results["documents"][0]
                distances = results["distances"][0] if results.get("distances") and results["distances"] else []
                metadatas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"] else []
                
                print(f"📄 Retrieved {len(retrieved_texts)} documents:")
                
                for j, (text, distance, metadata) in enumerate(zip(retrieved_texts, distances, metadatas), 1):
                    print(f"\n--- Document {j} (similarity: {1-distance:.3f}) ---")
                    
                    # Show metadata if available
                    if metadata:
                        source = metadata.get('source', 'Unknown')
                        print(f"Source: {source}")
                    
                    # Clean and show text
                    clean_text = text.replace('\n', ' ').replace('\t', ' ').strip()
                    
                    # Show first 400 characters
                    if len(clean_text) > 400:
                        print(f"Content: {clean_text[:400]}...")
                    else:
                        print(f"Content: {clean_text}")
                
                print(f"\n💡 Manual Evaluation:")
                print(f"   - Do these documents seem relevant to: '{question}'?")
                print(f"   - Do they contain information that could answer the question?")
                print(f"   - Are they readable and coherent?")
                
            else:
                print("❌ No documents retrieved")
        
        print("\n" + "=" * 80)
        print("🔍 MANUAL EVALUATION GUIDE")
        print("=" * 80)
        print("Look at the retrieved content above and evaluate:")
        print("1. Is the content relevant to the questions?")
        print("2. Is the text readable and coherent (not garbled)?")
        print("3. Does it contain technical information about MDS switches?")
        print("4. Could this information be used to answer the questions?")
        print("\nIf the content looks good, the RAG retrieval is working correctly!")
        print("The issue might be in how we format/present the final answers.")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_rag_validation()