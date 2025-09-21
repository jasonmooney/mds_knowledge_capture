#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Populating Vector Store with Local GPU Embeddings ===")

try:
    processor = RAGDocumentProcessor()
    
    print("✅ Processor initialized")
    print(f"   Embeddings: {type(processor.embeddings).__name__ if processor.embeddings else 'None'}")
    print(f"   Vector store: {type(processor.vector_store).__name__ if processor.vector_store else 'None'}")
    print()
    
    if not processor.embeddings:
        print("❌ No embeddings available")
        exit(1)
        
    if not processor.vector_store:
        print("❌ No vector store available")
        exit(1)
    
    print("🔄 Processing documents and generating embeddings...")
    result = processor.process_current_documents()
    
    print("\n📊 RESULTS:")
    print(f"   Total chunks: {result['total_chunks']}")
    print(f"   Files processed: {len(result['processed_files'])}")
    print(f"   Processing time: {result['processing_time']}")
    print(f"   Errors: {len(result['errors'])}")
    
    if result['errors']:
        print("\n❌ ERRORS:")
        for error in result['errors']:
            print(f"   - {error}")
    
    # Verify vector store population
    print("\n🔍 Verifying vector store...")
    collection = processor.vector_store.get_or_create_collection("mds_documents")
    count = collection.count()
    print(f"   Vector store contains: {count} documents")
    
    if count > 0:
        print(f"\n✅ SUCCESS! Vector store populated with {count} document chunks")
        print("   Ready for RAG queries!")
    else:
        print("\n❌ Vector store is still empty - check for errors above")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()