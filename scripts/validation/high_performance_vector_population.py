#!/usr/bin/env python3

import sys
import os
import time
import torch
from typing import List

# Add project root to path
sys.path.insert(0, os.getcwd())

print("=== High-Performance Vector Store Population ===")
print("Optimizing for RTX 5090 with 34GB VRAM")
print()

def populate_vector_store_optimized():
    """Optimized vector store population using maximum GPU power."""
    
    from src.rag_prep import RAGDocumentProcessor
    
    try:
        # Initialize with optimized settings for RTX 5090
        processor = RAGDocumentProcessor()
        
        if not processor.embeddings or not processor.vector_store:
            print("❌ Embeddings or vector store not available")
            return False
        
        print(f"✅ Using: {type(processor.embeddings).__name__}")
        
        # Load existing chunks from JSON (already processed)
        chunks_file = processor.vector_store_path / "chunks.json"
        if not chunks_file.exists():
            print("❌ No chunks file found - run document processing first")
            return False
        
        import json
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        texts = [chunk['content'] for chunk in chunks_data]
        metadatas = [chunk['metadata'] for chunk in chunks_data]
        
        print(f"📄 Loaded {len(texts)} text chunks from disk")
        print(f"🚀 Starting high-performance GPU embedding generation...")
        print()
        
        # Optimize for RTX 5090 - much larger batch sizes
        optimized_embedder = processor.embeddings
        original_batch_size = optimized_embedder.batch_size
        
        # Use much larger batch size for RTX 5090's 34GB VRAM
        optimized_embedder.batch_size = 128  # Increased from 64
        
        print(f"⚡ Optimized batch size: {optimized_embedder.batch_size}")
        print(f"🔥 Expected GPU utilization increase - monitor Task Manager!")
        print()
        
        # Generate embeddings with GPU monitoring
        start_time = time.time()
        
        # Force high GPU utilization
        with torch.cuda.device(0):
            torch.cuda.empty_cache()  # Clear cache for maximum memory
            
            print("🧠 Generating embeddings with maximum GPU power...")
            print("   (Check Task Manager - GPU should spike to higher utilization!)")
            
            embeddings = optimized_embedder.embed_documents(texts)
            
        generation_time = time.time() - start_time
        
        print(f"\n📊 EMBEDDING GENERATION COMPLETE:")
        print(f"   Time: {generation_time:.2f} seconds")
        print(f"   Rate: {len(texts)/generation_time:.1f} chunks/second")
        print(f"   GPU Memory Used: {torch.cuda.max_memory_allocated(0)/1e9:.2f}GB")
        print()
        
        # Store in ChromaDB with optimized batching
        print("💽 Storing in ChromaDB with batch optimization...")
        collection = processor.vector_store.get_or_create_collection("mds_documents")
        
        # Clear existing
        try:
            existing_count = collection.count()
            if existing_count > 0:
                print(f"Clearing {existing_count} existing chunks...")
                collection.delete(where={})
        except:
            pass
        
        # Store in large batches for better performance
        batch_size = 1000  # ChromaDB batch size
        total_stored = 0
        
        storage_start = time.time()
        
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            
            batch_texts = texts[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]
            batch_ids = [f"chunk_{j}" for j in range(i, batch_end)]
            
            collection.add(
                documents=batch_texts,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings,
                ids=batch_ids
            )
            
            total_stored += len(batch_texts)
            print(f"   Stored {total_stored}/{len(texts)} chunks ({total_stored/len(texts)*100:.1f}%)")
        
        storage_time = time.time() - storage_start
        total_time = generation_time + storage_time
        
        # Verify
        final_count = collection.count()
        
        print(f"\n🎉 HIGH-PERFORMANCE POPULATION COMPLETE!")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Embedding time: {generation_time:.2f}s ({len(texts)/generation_time:.1f} chunks/sec)")
        print(f"   Storage time: {storage_time:.2f}s")
        print(f"   Chunks stored: {final_count}")
        print(f"   Overall rate: {final_count/total_time:.1f} chunks/sec")
        print(f"   GPU max memory: {torch.cuda.max_memory_allocated(0)/1e9:.2f}GB")
        
        # Restore original batch size
        optimized_embedder.batch_size = original_batch_size
        
        return final_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_vector_store_optimized()
    
    if success:
        print("\n✅ Ready for RAG validation!")
    else:
        print("\n❌ Population failed - check errors above")