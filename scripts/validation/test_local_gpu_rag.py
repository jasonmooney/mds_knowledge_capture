#!/usr/bin/env python3

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Local GPU RAG Performance Test ===")
print(f"Test started at: {datetime.now()}")
print()

try:
    # Initialize processor with local GPU embeddings
    print("Initializing RAG processor with local GPU embeddings...")
    start_time = time.time()
    processor = RAGDocumentProcessor()
    setup_time = time.time() - start_time
    print(f"✅ Setup completed in {setup_time:.2f} seconds")
    print()
    
    # Check embedding type
    if hasattr(processor, 'embeddings') and processor.embeddings:
        embeddings_type = type(processor.embeddings).__name__
        print(f"Embedding system: {embeddings_type}")
        if hasattr(processor.embeddings, 'get_model_info'):
            model_info = processor.embeddings.get_model_info()
            print(f"Model: {model_info['model_name']}")
            print(f"Device: {model_info['device']} ({model_info.get('gpu_name', 'Unknown')})")
            print(f"Embedding dimension: {model_info['embedding_dimension']}")
            print(f"Batch size: {model_info['batch_size']}")
        print()
    
    # Process documents
    print("Processing documents...")
    processing_start = time.time()
    result = processor.process_current_documents()
    processing_time = time.time() - processing_start
    
    # Display results
    print("🚀 LOCAL GPU RAG PROCESSING COMPLETE!")
    print(f"Files processed: {len(result['processed_files'])}")
    print(f"Total chunks: {result['total_chunks']}")
    print(f"Processing time: {result['processing_time']}")
    print(f"Actual time: {processing_time:.2f} seconds")
    
    # Calculate performance
    if result['total_chunks'] > 0 and processing_time > 0:
        chunks_per_second = result['total_chunks'] / processing_time
        print(f"🏆 PERFORMANCE: {chunks_per_second:.1f} chunks/second")
        
        # Compare to previous cloud performance
        cloud_performance = 142.4  # chunks/second from previous run
        improvement = chunks_per_second / cloud_performance
        print(f"📈 Improvement vs cloud: {improvement:.1f}x faster")
    
    print()
    print("Errors:", len(result.get('errors', [])))
    if result.get('errors'):
        for error in result['errors']:
            print(f"  ❌ {error}")

except Exception as e:
    print(f"❌ Error during processing: {e}")
    import traceback
    traceback.print_exc()