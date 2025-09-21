"""
RAG (Retrieval-Augmented Generation) document preparation for MDS documentation.
Handles PDF chunking and vector store integration.
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

from metadata import MetadataManager

logger = logging.getLogger(__name__)


class RAGDocumentProcessor:
    """Processes documents for RAG (Retrieval-Augmented Generation)."""
    
    def __init__(
        self, 
        vector_store_path: str = "vector_store",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata_manager: Optional[MetadataManager] = None
    ):
        """Initialize RAG document processor."""
        self.vector_store_path = Path(vector_store_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.metadata_manager = metadata_manager or MetadataManager()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\\n\\n", "\\n", " ", ""]
        )
        
        # Initialize embeddings (requires OpenAI API key)
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            logger.warning(f"OpenAI embeddings not available: {e}")
            self.embeddings = None
        
        # Vector store will be initialized when first used
        self.vector_store = None
        
        logger.info(f"RAG processor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def load_and_chunk_pdf(self, pdf_path: str) -> List[Document]:
        """Load PDF and split into chunks."""
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
                    'source_path': pdf_path,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'processed_at': datetime.now().isoformat()
                })
            
            logger.info(f"PDF {pdf_name} split into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    def process_documents(self, document_paths: List[str]) -> List[Document]:
        """Process multiple PDF documents into chunks."""
        all_chunks = []
        
        for pdf_path in document_paths:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF not found: {pdf_path}")
                continue
                
            if not pdf_path.lower().endswith('.pdf'):
                logger.warning(f"Skipping non-PDF file: {pdf_path}")
                continue
            
            chunks = self.load_and_chunk_pdf(pdf_path)
            all_chunks.extend(chunks)
        
        logger.info(f"Total chunks created: {len(all_chunks)} from {len(document_paths)} documents")
        return all_chunks
    
    def initialize_vector_store(self) -> bool:
        """Initialize or load the vector store."""
        if not self.embeddings:
            logger.error("Embeddings not available, cannot initialize vector store")
            return False
        
        try:
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            
            # Try to load existing vector store
            if (self.vector_store_path / "index").exists():
                logger.info("Loading existing vector store")
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_path),
                    embedding_function=self.embeddings
                )
            else:
                logger.info("Creating new vector store")
                # Will be created when first documents are added
                self.vector_store = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            return False
    
    def add_documents_to_vector_store(self, chunks: List[Document]) -> bool:
        """Add document chunks to the vector store."""
        if not self.embeddings:
            logger.error("Embeddings not available")
            return False
        
        if not chunks:
            logger.warning("No chunks to add to vector store")
            return True
        
        try:
            if self.vector_store is None:
                # Create new vector store with first batch of documents
                logger.info("Creating vector store with initial documents")
                self.vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=str(self.vector_store_path)
                )
            else:
                # Add to existing vector store
                logger.info(f"Adding {len(chunks)} chunks to existing vector store")
                self.vector_store.add_documents(chunks)
            
            # Persist the vector store
            self.vector_store.persist()
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def process_current_documents(self) -> bool:
        """Process all current documents for RAG."""
        logger.info("Processing current documents for RAG")
        
        # Get current documents from metadata manager
        current_docs = self.metadata_manager.get_all_documents(current_only=True)
        
        if not current_docs:
            logger.info("No current documents to process")
            return True
        
        # Extract file paths
        pdf_paths = [doc['file_path'] for doc in current_docs if doc['file_path'].endswith('.pdf')]
        
        if not pdf_paths:
            logger.warning("No PDF files found in current documents")
            return True
        
        # Initialize vector store
        if not self.initialize_vector_store():
            return False
        
        # Process documents
        all_chunks = self.process_documents(pdf_paths)
        
        if not all_chunks:
            logger.warning("No chunks created from documents")
            return True
        
        # Add to vector store
        success = self.add_documents_to_vector_store(all_chunks)
        
        if success:
            # Save processing metadata
            self._save_processing_metadata(current_docs, len(all_chunks))
        
        return success
    
    def _save_processing_metadata(self, processed_docs: List[Dict], total_chunks: int) -> None:
        """Save metadata about RAG processing."""
        try:
            metadata = {
                'processed_at': datetime.now().isoformat(),
                'total_documents': len(processed_docs),
                'total_chunks': total_chunks,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'documents': [
                    {
                        'filename': doc['filename'],
                        'file_path': doc['file_path'],
                        'file_size': doc['file_size_bytes'],
                        'version': doc.get('version'),
                        'download_date': doc['download_date']
                    }
                    for doc in processed_docs
                ]
            }
            
            metadata_file = self.vector_store_path / "processing_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Processing metadata saved to {metadata_file}")
            
        except Exception as e:
            logger.error(f"Error saving processing metadata: {e}")
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant document chunks."""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            search_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content,
                    'source_file': doc.metadata.get('source_file'),
                    'chunk_index': doc.metadata.get('chunk_index'),
                    'similarity_score': score,
                    'metadata': doc.metadata
                }
                search_results.append(result)
            
            logger.info(f"Found {len(search_results)} relevant chunks for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_vector_store_info(self) -> Dict:
        """Get information about the current vector store."""
        if not self.vector_store:
            return {'status': 'not_initialized'}
        
        try:
            # Get basic info (collection count, etc.)
            info = {
                'status': 'active',
                'vector_store_path': str(self.vector_store_path),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
            
            # Try to get document count
            try:
                # This is a simplified way - actual implementation may vary
                collection = self.vector_store._collection
                info['document_count'] = collection.count()
            except:
                info['document_count'] = 'unknown'
            
            # Load processing metadata if available
            metadata_file = self.vector_store_path / "processing_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    processing_metadata = json.load(f)
                    info['last_processed'] = processing_metadata.get('processed_at')
                    info['total_documents'] = processing_metadata.get('total_documents')
                    info['total_chunks'] = processing_metadata.get('total_chunks')
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting vector store info: {e}")
            return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    # Simple validation test
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing RAG Document Processor...")
    
    # Test without OpenAI API key (will have limitations)
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = RAGDocumentProcessor(
            vector_store_path=f"{temp_dir}/vector_store",
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Test text splitter
        test_text = "This is a test document. " * 100  # Create long text
        test_doc = Document(page_content=test_text, metadata={'source': 'test'})
        
        chunks = processor.text_splitter.split_documents([test_doc])
        
        if chunks and len(chunks) > 1:
            print(f"✅ Text splitting works - created {len(chunks)} chunks")
            print(f"   First chunk length: {len(chunks[0].page_content)}")
        else:
            print("❌ Text splitting failed")
        
        # Test vector store info (without actual vector store)
        info = processor.get_vector_store_info()
        if info['status'] == 'not_initialized':
            print("✅ Vector store info retrieval works")
        else:
            print("❌ Vector store info unexpected")
    
    print("✅ RAG Document Processor validation complete")
    print("ℹ️  Note: Full functionality requires OpenAI API key for embeddings")