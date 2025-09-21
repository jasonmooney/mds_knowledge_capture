#!/usr/bin/env python3

import sys
import os
import torch
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

print("=== GPU Usage Investigation ===")
print(f"Test started at: {datetime.now()}")
print()

def check_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1e9
        cached = torch.cuda.memory_reserved(0) / 1e9
        print(f"GPU Memory - Allocated: {allocated:.2f}GB, Cached: {cached:.2f}GB")
    else:
        print("CUDA not available")

print("Initial GPU state:")
check_gpu_memory()
print()

try:
    # Test sentence-transformers GPU usage
    print("Loading sentence-transformers model...")
    from sentence_transformers import SentenceTransformer
    
    # Load model with explicit CUDA
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
    print("Model loaded")
    check_gpu_memory()
    print()
    
    # Test encoding with GPU monitoring
    test_texts = [
        "This is a test document for GPU usage monitoring",
        "Another test document to check CUDA utilization",
        "GPU should be actively processing these embeddings",
        "Monitoring GPU utilization during sentence encoding",
        "Testing CUDA acceleration with sentence transformers"
    ] * 20  # 100 texts total
    
    print(f"Encoding {len(test_texts)} texts...")
    print("Check Task Manager GPU utilization NOW!")
    
    start_time = time.time()
    
    # Force CUDA usage and monitor
    with torch.cuda.device(0):
        # Create CUDA events for precise timing
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        
        start_event.record()
        embeddings = model.encode(test_texts, convert_to_tensor=True, device='cuda', show_progress_bar=True)
        end_event.record()
        
        torch.cuda.synchronize()
        cuda_time = start_event.elapsed_time(end_event) / 1000  # Convert to seconds
    
    total_time = time.time() - start_time
    
    print(f"\nResults:")
    print(f"Total texts encoded: {len(test_texts)}")
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Embeddings device: {embeddings.device}")
    print(f"CUDA time: {cuda_time:.3f}s")
    print(f"Total time: {total_time:.3f}s")
    print(f"Rate: {len(test_texts)/total_time:.1f} texts/second")
    
    print("\nFinal GPU state:")
    check_gpu_memory()
    
    # Test if embeddings are actually on GPU
    if embeddings.is_cuda:
        print("✅ Embeddings are on GPU")
    else:
        print("❌ Embeddings are NOT on GPU")
        
    # Check model device
    print(f"Model device: {model.device}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()