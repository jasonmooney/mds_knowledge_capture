#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Vector Store Status Check ===")

try:
    processor = RAGDocumentProcessor()
    
    print(f"Vector store available: {processor.vector_store is not None}")
    
    if processor.vector_store:
        # Check the collection
        collection = processor.vector_store.get_or_create_collection("mds_documents")
        count = collection.count()
        
        print(f"Collection name: mds_documents")
        print(f"Document count: {count}")
        
        if count == 0:
            print("\n❌ VECTOR STORE IS EMPTY!")
            print("The embeddings were generated but not stored in ChromaDB.")
            print("Need to re-run the RAG processing to populate the vector store.")
        else:
            print(f"\n✅ Vector store contains {count} document chunks")
            
            # Get a sample document
            sample = collection.peek(limit=1)
            if sample and sample['documents']:
                print(f"Sample document: {sample['documents'][0][:100]}...")
    else:
        print("❌ Vector store is not initialized")
        
except Exception as e:
    print(f"Error checking vector store: {e}")
    import traceback
    traceback.print_exc()