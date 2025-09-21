#!/usr/bin/env python3

import sys
import os
import time
import torch
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.local_gpu_embeddings import LocalGPUEmbeddings

print("=== Maximum GPU Performance Test ===")
print("Testing RTX 5090 with massive workloads")
print()

def stress_test_gpu():
    """Stress test the GPU with massive embedding workloads."""
    
    try:
        # Initialize with maximum performance settings
        print("🚀 Initializing with RTX 5090 optimizations...")
        
        embedder = LocalGPUEmbeddings(
            model_name="sentence-transformers/all-roberta-large-v1",  # Large model
            device="cuda",
            batch_size=256  # Massive batch size for RTX 5090
        )
        
        model_info = embedder.get_model_info()
        print(f"Model: {model_info['model_name']}")
        print(f"Device: {model_info['device']} - {model_info['gpu_name']}")
        print(f"Batch size: {model_info['batch_size']} (MAXIMIZED)")
        print(f"Embedding dim: {model_info['embedding_dimension']}")
        print()
        
        # Create massive test workload
        base_text = """
        This is a comprehensive test document for the Cisco MDS 9000 series switches 
        running NX-OS software. The document covers configuration, troubleshooting, 
        hardware specifications, EPLD firmware, FCoE configuration, SAN analytics, 
        telemetry streaming, port channels, VSAN configuration, zoning, inter-VSAN 
        routing, intelligent storage services, quality of service, and comprehensive 
        monitoring capabilities for enterprise storage area networks.
        """
        
        # Create different workload sizes to test scalability
        test_sizes = [500, 1000, 2000, 5000]  # Start smaller and ramp up
        
        for size in test_sizes:
            print(f"🔥 STRESS TEST: Processing {size} documents")
            print(f"   Expected GPU utilization spike - WATCH TASK MANAGER!")
            print(f"   Batch size: {embedder.batch_size}")
            print()
            
            # Create large dataset
            test_texts = [f"{base_text} Document ID: {i}" for i in range(size)]
            
            # Clear GPU cache for maximum memory usage
            torch.cuda.empty_cache()
            
            # Monitor GPU memory before
            if torch.cuda.is_available():
                initial_memory = torch.cuda.memory_allocated(0) / 1e9
                print(f"   GPU memory before: {initial_memory:.3f}GB")
            
            # Time the operation
            start_time = time.time()
            
            # Force maximum GPU utilization
            with torch.cuda.device(0):
                print(f"   🚀 STARTING GPU PROCESSING - CHECK TASK MANAGER NOW!")
                embeddings = embedder.embed_documents(test_texts)
            
            elapsed = time.time() - start_time
            
            # Monitor GPU memory after
            if torch.cuda.is_available():
                final_memory = torch.cuda.memory_allocated(0) / 1e9
                max_memory = torch.cuda.max_memory_allocated(0) / 1e9
                print(f"   GPU memory after: {final_memory:.3f}GB")
                print(f"   GPU memory peak: {max_memory:.3f}GB")
                torch.cuda.reset_peak_memory_stats()
            
            # Results
            rate = len(test_texts) / elapsed
            print(f"   ⚡ RESULTS: {elapsed:.2f}s, {rate:.1f} docs/sec")
            print(f"   📊 Generated {len(embeddings)} embeddings")
            print()
            
            # Brief pause between tests
            time.sleep(2)
        
        print("🎉 GPU STRESS TEST COMPLETE!")
        print("If GPU utilization stayed low, the model might be too efficient for the RTX 5090!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def quick_vector_store_test():
    """Quick test with existing processed documents."""
    
    print("\n=== Quick Vector Store Population Test ===")
    
    try:
        # Load just a sample of documents for quick testing
        documents_path = Path("knowledge_source/current")
        if not documents_path.exists():
            print("❌ No documents directory found")
            return
        
        pdf_files = list(documents_path.glob("*.pdf"))[:3]  # Just first 3 PDFs
        
        if not pdf_files:
            print("❌ No PDF files found")
            return
        
        print(f"📄 Testing with {len(pdf_files)} PDF files")
        
        from src.rag_prep import RAGDocumentProcessor
        
        # Process just a few files quickly
        processor = RAGDocumentProcessor()
        
        # Process each PDF
        all_texts = []
        for pdf_file in pdf_files:
            print(f"   Processing: {pdf_file.name}")
            chunks = processor.load_and_chunk_pdf(str(pdf_file))
            texts = [chunk.page_content for chunk in chunks[:50]]  # Just 50 chunks each
            all_texts.extend(texts)
        
        print(f"📊 Total text chunks for embedding: {len(all_texts)}")
        
        if processor.embeddings and len(all_texts) > 0:
            print("🚀 Generating embeddings - WATCH GPU!")
            
            start_time = time.time()
            embeddings = processor.embeddings.embed_documents(all_texts)
            elapsed = time.time() - start_time
            
            print(f"✅ Generated {len(embeddings)} embeddings in {elapsed:.2f}s")
            print(f"   Rate: {len(embeddings)/elapsed:.1f} embeddings/sec")
            
            # Try storing in ChromaDB
            if processor.vector_store:
                print("💽 Storing in vector database...")
                collection = processor.vector_store.get_or_create_collection("mds_test")
                
                # Clear and add
                try:
                    collection.delete(where={})
                except:
                    pass
                
                ids = [f"test_chunk_{i}" for i in range(len(all_texts))]
                metadatas = [{"source": f"test_{i}"} for i in range(len(all_texts))]
                
                collection.add(
                    documents=all_texts,
                    embeddings=embeddings,
                    ids=ids,
                    metadatas=metadatas
                )
                
                count = collection.count()
                print(f"✅ Stored {count} documents in vector store")
                
                # Test search
                test_query = "How to configure FCoE on MDS switches?"
                query_embedding = processor.embeddings.embed_query(test_query)
                
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3
                )
                
                print(f"🔍 Test search returned {len(results['documents'][0])} results")
                if results['documents'][0]:
                    print(f"   Sample result: {results['documents'][0][0][:100]}...")
        
    except Exception as e:
        print(f"❌ Error in quick test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run GPU stress test first
    stress_test_gpu()
    
    # Then try quick vector store test
    quick_vector_store_test()