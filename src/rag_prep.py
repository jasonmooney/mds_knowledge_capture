"""
RAG (Retrieval-Augmented Generation) document preparation for MDS documentation.
Handles PDF chunking and basic text processing (vector store disabled for now).
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    try:
        from langchain.document_loaders import PyPDFLoader
    except ImportError:
        PyPDFLoader = None

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.metadata import MetadataManager

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
        
        # Initialize embeddings with OpenRouter
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_api_key:
            try:
                from langchain_openai import OpenAIEmbeddings
                # Set environment variable for OpenAI client
                os.environ["OPENAI_API_KEY"] = openrouter_api_key
                os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
                
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-3-small"  # Use OpenAI embedding model via OpenRouter
                )
                logger.info("✅ OpenRouter embeddings initialized")
            except ImportError as e:
                logger.warning(f"OpenAI embeddings not available: {e}")
                self.embeddings = None
        else:
            logger.warning("OPENROUTER_API_KEY not found in environment")
            self.embeddings = None
            
        # Initialize vector store if we have embeddings
        if self.embeddings:
            try:
                import chromadb
                self.vector_store_path.mkdir(parents=True, exist_ok=True)
                self.vector_store = chromadb.PersistentClient(path=str(self.vector_store_path / "chroma_db"))
                logger.info("✅ ChromaDB vector store initialized")
            except ImportError as e:
                logger.warning(f"ChromaDB not available: {e}")
                self.vector_store = None
        else:
            self.vector_store = None
        
        logger.info("✅ RAG processor initialized with full functionality")
    
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
                    'processed_at': datetime.now().isoformat()
                })
            
            logger.info(f"✅ Created {len(chunks)} chunks from {pdf_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    def process_current_documents(self, documents_path: str = "knowledge_source/current") -> Dict[str, any]:
        """Process all current documents for RAG."""
        logger.info("🔄 Processing current documents for RAG...")
        
        documents_path = Path(documents_path)
        if not documents_path.exists():
            logger.error(f"Documents path does not exist: {documents_path}")
            return {'error': 'Documents path not found'}
        
        results = {
            'processed_files': [],
            'total_chunks': 0,
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
        
        # Save chunks to JSON for now (since vector store is disabled)
        if all_chunks:
            chunks_output_path = self.vector_store_path / "chunks.json"
            chunks_output_path.parent.mkdir(parents=True, exist_ok=True)
            
            chunks_data = []
            for chunk in all_chunks:
                chunks_data.append({
                    'content': chunk.page_content,
                    'metadata': chunk.metadata
                })
            
            with open(chunks_output_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved {len(chunks_data)} chunks to {chunks_output_path}")
        
        end_time = datetime.now()
        results['processing_time'] = str(end_time - start_time)
        
        logger.info(f"✅ RAG processing complete:")
        logger.info(f"   📁 Files processed: {len(results['processed_files'])}")
        logger.info(f"   📄 Total chunks: {results['total_chunks']}")
        logger.info(f"   ⏱️  Processing time: {results['processing_time']}")
        logger.info(f"   ❌ Errors: {len(results['errors'])}")
        
        return results
    
    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search chunks (basic text search since vector search is disabled)."""
        chunks_file = self.vector_store_path / "chunks.json"
        
        if not chunks_file.exists():
            logger.warning("No chunks file found. Run process_current_documents first.")
            return []
        
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Basic text search (case-insensitive)
            query_lower = query.lower()
            matches = []
            
            for chunk in chunks_data:
                content_lower = chunk['content'].lower()
                if query_lower in content_lower:
                    # Simple relevance scoring based on query word count
                    score = content_lower.count(query_lower) / len(chunk['content'].split())
                    matches.append({
                        'content': chunk['content'][:500] + '...' if len(chunk['content']) > 500 else chunk['content'],
                        'metadata': chunk['metadata'],
                        'relevance_score': score
                    })
            
            # Sort by relevance and return top_k
            matches.sort(key=lambda x: x['relevance_score'], reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about processed documents."""
        chunks_file = self.vector_store_path / "chunks.json"
        
        if not chunks_file.exists():
            return {'status': 'No processed documents found'}
        
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Collect statistics
            files = set()
            total_chars = 0
            chunk_sizes = []
            
            for chunk in chunks_data:
                files.add(chunk['metadata']['source_file'])
                total_chars += len(chunk['content'])
                chunk_sizes.append(len(chunk['content']))
            
            return {
                'total_chunks': len(chunks_data),
                'unique_files': len(files),
                'total_characters': total_chars,
                'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
                'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
                'files': list(files)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}


def main():
    """Test the RAG processor."""
    logging.basicConfig(level=logging.INFO)
    
    processor = RAGDocumentProcessor()
    
    # Process current documents
    results = processor.process_current_documents()
    
    print("\\n📊 RAG Processing Results:")
    print("=" * 50)
    print(f"Files processed: {len(results['processed_files'])}")
    print(f"Total chunks: {results['total_chunks']}")
    print(f"Processing time: {results['processing_time']}")
    
    if results['errors']:
        print(f"\\n❌ Errors:")
        for error in results['errors']:
            print(f"  • {error}")
    
    # Show statistics
    stats = processor.get_stats()
    if 'error' not in stats:
        print(f"\\n📈 Statistics:")
        print(f"  • Unique files: {stats['unique_files']}")
        print(f"  • Average chunk size: {stats['avg_chunk_size']:.0f} chars")
        print(f"  • Total characters: {stats['total_characters']:,}")
    
    # Test search
    print(f"\\n🔍 Testing search...")
    search_results = processor.search_chunks("VSAN", top_k=3)
    print(f"Found {len(search_results)} results for 'VSAN'")
    
    for i, result in enumerate(search_results, 1):
        print(f"\\n{i}. Score: {result['relevance_score']:.4f}")
        print(f"   Source: {result['metadata']['source_file']}")
        print(f"   Content: {result['content'][:150]}...")


if __name__ == "__main__":
    main()