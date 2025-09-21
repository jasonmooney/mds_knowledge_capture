"""
Local GPU Embeddings using Sentence Transformers for high-performance embedding generation.
Optimized for NVIDIA RTX 5090 with 34GB VRAM.
Compatible with LangChain embedding interface.
"""

import torch
import logging
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class LocalGPUEmbeddings:
    """High-performance local GPU embeddings using Sentence Transformers."""
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize local GPU embeddings.
        
        Args:
            model_name: HuggingFace model name for embeddings
            device: Device to use ('cuda', 'cpu', or None for auto)
            batch_size: Batch size for processing chunks
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing local GPU embeddings with model: {model_name}")
        logger.info(f"Target device: {self.device}")
        
        # Load model
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info(f"Successfully loaded {model_name} on {self.device}")
            
            if torch.cuda.is_available() and self.device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"Using GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents (LangChain compatible method).
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        logger.info(f"Embedding {len(texts)} documents on {self.device}")
        
        # Force GPU memory allocation monitoring
        if self.device == "cuda":
            initial_memory = torch.cuda.memory_allocated(0) / 1e9
            logger.info(f"GPU memory before embedding: {initial_memory:.3f}GB")
        
        start_time = torch.cuda.Event(enable_timing=True) if self.device == "cuda" else None
        end_time = torch.cuda.Event(enable_timing=True) if self.device == "cuda" else None
        
        try:
            if start_time:
                start_time.record()
                
            # Process in batches for memory efficiency with explicit GPU usage
            embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Force CUDA processing and keep tensors on GPU during computation
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_tensor=True,  # Keep as CUDA tensors during processing
                    device=self.device,      # Explicitly specify device
                    show_progress_bar=False,
                    batch_size=self.batch_size,
                    normalize_embeddings=True  # GPU-accelerated normalization
                )
                
                # Convert to list only after GPU processing is complete
                embeddings.extend(batch_embeddings.cpu().tolist())
                
                if i % (self.batch_size * 5) == 0:  # Log every 5 batches
                    current_memory = torch.cuda.memory_allocated(0) / 1e9 if self.device == "cuda" else 0
                    logger.info(f"Processed {i + len(batch)}/{len(texts)} documents, GPU memory: {current_memory:.3f}GB")
            
            if end_time and start_time:
                end_time.record()
                torch.cuda.synchronize()  # Ensure all CUDA operations complete
                elapsed_ms = start_time.elapsed_time(end_time)
                rate = len(texts) / (elapsed_ms / 1000)
                logger.info(f"🚀 GPU embedding rate: {rate:.1f} docs/second ({elapsed_ms:.1f}ms total)")
                
                final_memory = torch.cuda.memory_allocated(0) / 1e9
                logger.info(f"GPU memory after embedding: {final_memory:.3f}GB")
            
            logger.info(f"Successfully embedded {len(texts)} documents using {self.device.upper()}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error during embedding: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query (LangChain compatible method).
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.model.encode([text], convert_to_tensor=False)
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "max_seq_length": self.model.max_seq_length,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        }


# Recommended models for different use cases
EMBEDDING_MODELS = {
    "fast": "all-MiniLM-L6-v2",  # Fast, lightweight, good quality
    "balanced": "all-mpnet-base-v2",  # Good balance of speed and quality
    "quality": "all-MiniLM-L12-v2",  # Higher quality, slower
    "large": "sentence-transformers/all-roberta-large-v1"  # Highest quality, requires more VRAM
}


def get_recommended_model(gpu_memory_gb: float = 34.0) -> str:
    """Get recommended model based on available GPU memory."""
    if gpu_memory_gb >= 20:
        return EMBEDDING_MODELS["large"]
    elif gpu_memory_gb >= 8:
        return EMBEDDING_MODELS["quality"] 
    elif gpu_memory_gb >= 4:
        return EMBEDDING_MODELS["balanced"]
    else:
        return EMBEDDING_MODELS["fast"]