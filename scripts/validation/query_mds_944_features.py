#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== RAG Query: Features Added to MDS 9.4.4 ===")
print()

def query_mds_features():
    """Query the RAG system about MDS 9.4.4 features."""
    
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
        
        # Specific query about 9.4.4 features
        questions = [
            "What features were added in MDS 9.4.4?",
            "What's new in Cisco MDS 9.4.4 release?", 
            "MDS 9.4.4 new features and enhancements",
            "Cisco MDS 9.4.4 release notes features"
        ]
        
        print(f"🔍 Searching for information about MDS 9.4.4 features...")
        print("=" * 70)
        
        for i, question in enumerate(questions, 1):
            print(f"\nQuery {i}: {question}")
            print("-" * 50)
            
            # Retrieve relevant documents
            query_embedding = processor.embeddings.embed_query(question)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["documents", "distances", "metadatas"]
            )
            
            if results and results["documents"] and results["documents"][0]:
                retrieved_texts = results["documents"][0]
                distances = results["distances"][0] if results.get("distances") and results["distances"] else []
                metadatas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"] else []
                
                print(f"📄 Found {len(retrieved_texts)} relevant documents:")
                
                best_match = None
                best_similarity = 0
                
                for j, (text, distance, metadata) in enumerate(zip(retrieved_texts, distances, metadatas), 1):
                    similarity = 1 - distance
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = text
                    
                    print(f"\n--- Document {j} (similarity: {similarity:.3f}) ---")
                    
                    # Show metadata if available
                    if metadata:
                        source = metadata.get('source', 'Unknown')
                        print(f"Source: {source}")
                    
                    # Clean and show text - look for 9.4.4 mentions
                    clean_text = text.replace('\n', ' ').replace('\t', ' ').strip()
                    
                    # Highlight if it mentions 9.4.4 specifically
                    if "9.4.4" in clean_text:
                        print("🎯 CONTAINS 9.4.4 REFERENCE!")
                    
                    # Show content with focus on 9.4.4 context
                    if len(clean_text) > 600:
                        # Try to find 9.4.4 context
                        if "9.4.4" in clean_text:
                            # Find context around 9.4.4
                            idx = clean_text.find("9.4.4")
                            start = max(0, idx - 200)
                            end = min(len(clean_text), idx + 400)
                            context = clean_text[start:end]
                            print(f"Content (around 9.4.4): ...{context}...")
                        else:
                            print(f"Content: {clean_text[:600]}...")
                    else:
                        print(f"Content: {clean_text}")
                
                # If we found a good match, break after first query
                if best_similarity > 0.3 and best_match and "9.4.4" in best_match:
                    print(f"\n🎯 Found strong match with 9.4.4 reference (similarity: {best_similarity:.3f})")
                    print("Stopping search - found relevant information!")
                    break
                
            else:
                print("❌ No documents retrieved for this query")
        
        print("\n" + "=" * 70)
        print("🔍 SEARCH SUMMARY")
        print("=" * 70)
        print("The system searched for information about MDS 9.4.4 features.")
        print("Look for documents marked '🎯 CONTAINS 9.4.4 REFERENCE!' above.")
        print("These should contain the most relevant information about 9.4.4 features.")
        
    except Exception as e:
        print(f"❌ Error during query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_mds_features()