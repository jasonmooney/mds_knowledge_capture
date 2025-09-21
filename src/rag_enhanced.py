"""
Enhanced RAG (Retrieval-Augmented Generation) document processor with full ChromaDB support.
This version includes vector embeddings, semantic search, and advanced query capabilities.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import uuid

try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    try:
        from langchain.document_loaders import PyPDFLoader
    except ImportError:
        PyPDFLoader = None

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ChromaDB imports
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# OpenAI embeddings for semantic similarity
try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from metadata import MetadataManager

logger = logging.getLogger(__name__)


class EnhancedRAGProcessor:
    """Enhanced RAG processor with ChromaDB vector database support."""
    
    def __init__(
        self, 
        vector_store_path: str = "chroma_db",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "mds_documents",
        metadata_manager: Optional[MetadataManager] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize enhanced RAG processor with ChromaDB."""
        self.vector_store_path = Path(vector_store_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        self.metadata_manager = metadata_manager or MetadataManager()
        self.embedding_model = embedding_model
        
        # Check if PyPDFLoader is available
        if PyPDFLoader is None:
            logger.warning("PyPDFLoader not available. Install langchain-community.")
            self.pdf_loader_available = False
        else:
            self.pdf_loader_available = True
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\\n\\n", "\\n", " ", ""]
        )
        
        # Initialize ChromaDB
        self._initialize_chromadb()
        
        logger.info("✅ Enhanced RAG processor initialized with ChromaDB support")
        logger.info(f"   📊 Collection: {self.collection_name}")
        logger.info(f"   📁 Vector store: {self.vector_store_path}")
        logger.info(f"   🔍 Embedding model: {self.embedding_model}")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create vector store directory
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_store_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize embedding function
            # Use sentence transformers for better embeddings
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"📚 Connected to existing collection: {self.collection_name}")
            except Exception as e:
                # Collection doesn't exist, create it
                logger.info(f"Creating new collection (error: {e})")
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "MDS documentation chunks"}
                )
                logger.info(f"📚 Created new collection: {self.collection_name}")
            
            # Check collection stats
            count = self.collection.count()
            logger.info(f"📊 Collection contains {count} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None
    
    def load_and_chunk_pdf(self, pdf_path: str) -> List[Document]:
        """Load PDF and split into chunks."""
        if not self.pdf_loader_available:
            logger.error("PDF loading not available. Install langchain-community.")
            return []
            
        try:
            logger.info(f"Loading PDF: {pdf_path}")
            
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            if not pages:
                logger.warning(f"No content loaded from {pdf_path}")
                return []
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(pages)
            
            # Add metadata to chunks
            pdf_name = Path(pdf_path).name
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'source_file': pdf_name,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'processed_at': datetime.now().isoformat(),
                    'file_path': str(pdf_path)
                })
            
            logger.info(f"✅ Created {len(chunks)} chunks from {pdf_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    def add_documents_to_vector_store(self, chunks: List[Document]) -> bool:
        """Add document chunks to ChromaDB vector store."""
        if not self.collection:
            logger.error("ChromaDB collection not available")
            return False
        
        try:
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # Create unique ID for each chunk
                chunk_id = f"{chunk.metadata['source_file']}_{chunk.metadata['chunk_id']}_{uuid.uuid4().hex[:8]}"
                
                documents.append(chunk.page_content)
                metadatas.append(chunk.metadata)
                ids.append(chunk_id)
            
            # Add to collection in batches (ChromaDB has batch limits)
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
            logger.info(f"✅ Added {len(documents)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def process_current_documents(self, documents_path: str = "knowledge_source/current") -> Dict[str, Any]:
        """Process all current documents for RAG with vector storage."""
        logger.info("🔄 Processing current documents for enhanced RAG...")
        
        documents_path = Path(documents_path)
        if not documents_path.exists():
            logger.error(f"Documents path does not exist: {documents_path}")
            return {'error': 'Documents path not found'}
        
        results = {
            'processed_files': [],
            'total_chunks': 0,
            'vector_store_chunks': 0,
            'errors': [],
            'processing_time': None
        }
        
        start_time = datetime.now()
        
        # Find all PDF files
        pdf_files = list(documents_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("No PDF files found in documents directory")
            return results
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        all_chunks = []
        
        for pdf_file in pdf_files:
            try:
                # Check if file is already processed (based on modification time)
                file_id = f"{pdf_file.name}_{pdf_file.stat().st_mtime}"
                
                chunks = self.load_and_chunk_pdf(str(pdf_file))
                
                if chunks:
                    all_chunks.extend(chunks)
                    results['processed_files'].append({
                        'file': pdf_file.name,
                        'chunks': len(chunks),
                        'size_bytes': pdf_file.stat().st_size
                    })
                    results['total_chunks'] += len(chunks)
                else:
                    results['errors'].append(f"No chunks created from {pdf_file.name}")
                    
            except Exception as e:
                error_msg = f"Failed to process {pdf_file.name}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Add all chunks to vector store
        if all_chunks and self.collection:
            success = self.add_documents_to_vector_store(all_chunks)
            if success:
                results['vector_store_chunks'] = len(all_chunks)
            else:
                results['errors'].append("Failed to add documents to vector store")
        
        # Also save chunks to JSON as backup
        if all_chunks:
            backup_path = self.vector_store_path / "chunks_backup.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            chunks_data = []
            for chunk in all_chunks:
                chunks_data.append({
                    'content': chunk.page_content,
                    'metadata': chunk.metadata
                })
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved backup of {len(chunks_data)} chunks to {backup_path}")
        
        end_time = datetime.now()
        results['processing_time'] = str(end_time - start_time)
        
        logger.info(f"✅ Enhanced RAG processing complete:")
        logger.info(f"   📁 Files processed: {len(results['processed_files'])}")
        logger.info(f"   📄 Total chunks: {results['total_chunks']}")
        logger.info(f"   🗄️  Vector store chunks: {results['vector_store_chunks']}")
        logger.info(f"   ⏱️  Processing time: {results['processing_time']}")
        logger.info(f"   ❌ Errors: {len(results['errors'])}")
        
        return results
    
    def search_chunks(self, query: str, top_k: int = 5, where: Optional[Dict] = None) -> List[Dict]:
        """Search chunks using semantic similarity via ChromaDB."""
        if not self.collection:
            logger.error("ChromaDB collection not available")
            return []
        
        try:
            logger.info(f"🔍 Searching for: '{query}' (top {top_k} results)")
            
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,  # Optional metadata filtering
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (lower distance = higher similarity)
                    similarity_score = 1.0 - distance
                    
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'rank': i + 1
                    })
            
            logger.info(f"✅ Found {len(formatted_results)} semantic matches")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents and vector store."""
        stats = {
            'vector_store_available': self.collection is not None,
            'embedding_model': self.embedding_model,
            'collection_name': self.collection_name
        }
        
        if self.collection:
            try:
                count = self.collection.count()
                stats['total_vectors'] = count
                
                if count > 0:
                    # Get sample to analyze metadata
                    sample = self.collection.get(limit=min(100, count), include=["metadatas"])
                    
                    if sample['metadatas']:
                        files = set()
                        for metadata in sample['metadatas']:
                            if 'source_file' in metadata:
                                files.add(metadata['source_file'])
                        
                        stats['unique_files'] = len(files)
                        stats['sample_files'] = list(files)[:10]  # First 10 files
                else:
                    stats['unique_files'] = 0
                    stats['sample_files'] = []
                
            except Exception as e:
                stats['error'] = str(e)
        
        # Check backup file
        backup_path = self.vector_store_path / "chunks_backup.json"
        if backup_path.exists():
            stats['backup_available'] = True
            stats['backup_size_mb'] = backup_path.stat().st_size / (1024 * 1024)
        else:
            stats['backup_available'] = False
        
        return stats
    
    def clear_vector_store(self) -> bool:
        """Clear all documents from the vector store."""
        if not self.collection:
            logger.error("ChromaDB collection not available")
            return False
        
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "MDS documentation chunks"}
            )
            logger.info(f"🗑️ Cleared vector store collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False


def main():
    """Test the enhanced RAG processor."""
    logging.basicConfig(level=logging.INFO)
    
    processor = EnhancedRAGProcessor()
    
    # Process current documents
    results = processor.process_current_documents()
    
    print("\\n📊 Enhanced RAG Processing Results:")
    print("=" * 60)
    print(f"Files processed: {len(results['processed_files'])}")
    print(f"Total chunks: {results['total_chunks']}")
    print(f"Vector store chunks: {results['vector_store_chunks']}")
    print(f"Processing time: {results['processing_time']}")
    
    if results['errors']:
        print(f"\\n❌ Errors:")
        for error in results['errors']:
            print(f"  • {error}")
    
    # Show statistics
    stats = processor.get_stats()
    print(f"\\n📈 Vector Store Statistics:")
    print(f"  • Available: {stats['vector_store_available']}")
    print(f"  • Total vectors: {stats.get('total_vectors', 'N/A')}")
    print(f"  • Unique files: {stats.get('unique_files', 'N/A')}")
    print(f"  • Embedding model: {stats['embedding_model']}")
    print(f"  • Backup available: {stats['backup_available']}")
    
    # Test semantic search
    test_queries = [
        "VSAN configuration",
        "fabric binding setup", 
        "NX-OS commands",
        "MDS switch management"
    ]
    
    print(f"\\n🔍 Testing Semantic Search:")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\\nQuery: '{query}'")
        search_results = processor.search_chunks(query, top_k=3)
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                print(f"  {i}. Score: {result['similarity_score']:.4f}")
                print(f"     Source: {result['metadata']['source_file']}")
                print(f"     Content: {result['content'][:100]}...")
        else:
            print("  No results found")


if __name__ == "__main__":
    main()