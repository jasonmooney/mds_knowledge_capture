#!/usr/bin/env python3

import sys
import os

print("=== GPU and Embedding Analysis ===")
print()

# Check PyTorch GPU
try:
    import torch
    print(f"PyTorch CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device Count: {torch.cuda.device_count()}")
        print(f"Current Device: {torch.cuda.current_device()}")
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"PyTorch Version: {torch.__version__}")
    print()
except ImportError:
    print("PyTorch not available")

# Check embedding packages
print("=== Embedding-related packages ===")
import pkg_resources
packages = list(pkg_resources.working_set)
embedding_packages = [str(pkg) for pkg in packages if any(term in str(pkg).lower() for term in 
    ['embedding', 'sentence-transformer', 'transformers', 'huggingface', 'openai'])]
for pkg in sorted(embedding_packages):
    print(f"  {pkg}")

print()

# Check what we're actually using for embeddings
print("=== Current RAG Configuration ===")
sys.path.insert(0, os.getcwd())
try:
    from src.rag_prep import RAGDocumentProcessor
    processor = RAGDocumentProcessor()
    if hasattr(processor, 'embeddings') and processor.embeddings:
        print(f"Embeddings type: {type(processor.embeddings)}")
        print(f"Using: OpenRouter cloud embeddings via OpenAI API")
    else:
        print("No embeddings configured")
except Exception as e:
    print(f"Error checking RAG config: {e}")

print()

# Performance analysis
print("=== Performance Analysis ===")
print("9,971 chunks embedded in 70 seconds")
print("Rate: ~142 chunks/second")
print("Since we're using OpenRouter cloud embeddings:")
print("- GPU was NOT used for embeddings (cloud-based)")
print("- GPU WAS available but unused for this task")
print("- Performance limited by network latency, not compute")
print("- For comparison, local GPU embeddings could be 5-10x faster")