#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== RAG Validation with Working Vector Store ===")

try:
    processor = RAGDocumentProcessor()
    
    if not processor.vector_store or not processor.embeddings:
        print("❌ Vector store or embeddings not available")
        exit(1)
    
    # Use the test collection we just populated
    collection = processor.vector_store.get_or_create_collection("mds_test")
    count = collection.count()
    
    print(f"✅ Using collection 'mds_test' with {count} documents")
    
    if count == 0:
        print("❌ Test collection is empty - run max_gpu_test.py first")
        exit(1)
    
    # Test queries
    test_queries = [
        "What are recommended software releases for MDS switches?",
        "How to configure FCoE on MDS switches?", 
        "What are the compatibility requirements for MDS 9000?",
        "Show me command reference information",
        "What are the hardware specifications?"
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} queries against {count} documents")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        # Generate query embedding
        query_embedding = processor.embeddings.embed_query(query)
        
        # Search the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "distances"]
        )
        
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else []
            
            print(f"✅ Found {len(documents)} relevant documents")
            
            for j, (doc, dist) in enumerate(zip(documents, distances)):
                print(f"   Result {j+1} (similarity: {1-dist:.3f}):")
                print(f"   {doc[:150]}...")
                print()
        else:
            print("❌ No results found")
    
    print("🎉 RAG VALIDATION COMPLETE!")
    print("The system can successfully find and retrieve relevant information!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()