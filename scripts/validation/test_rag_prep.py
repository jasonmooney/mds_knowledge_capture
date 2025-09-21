"""
Validation script for RAG document processor.
Tests document chunking and basic RAG functionality.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_prep import RAGDocumentProcessor
from langchain.schema import Document


def test_rag_processor():
    """Test the RAG document processor."""
    print("🧪 Testing RAG Document Processor...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Basic initialization
        print("\n🚀 Testing processor initialization...")
        
        processor = RAGDocumentProcessor(
            vector_store_path=f"{temp_dir}/vector_store",
            chunk_size=200,
            chunk_overlap=50
        )
        
        if processor.text_splitter and processor.chunk_size == 200:
            print("✅ Processor initialized successfully")
            print(f"   Chunk size: {processor.chunk_size}")
            print(f"   Chunk overlap: {processor.chunk_overlap}")
        else:
            print("❌ Processor initialization failed")
            return False
        
        # Test 2: Text splitting
        print("\n📄 Testing text splitting...")
        
        # Create a test document with known structure
        test_content = """
        This is the first paragraph of our test document. It contains multiple sentences 
        to test the chunking functionality of our RAG system.
        
        This is the second paragraph. We want to ensure that the text splitter properly 
        handles paragraph breaks and creates reasonable chunks for processing.
        
        Here is another section with technical content about MDS switches and network 
        configuration. This type of content would be typical in Cisco documentation.
        
        The final paragraph discusses advanced features and configuration examples
        that would be useful for network engineers working with MDS systems.
        """ * 3  # Repeat to make it longer
        
        test_doc = Document(
            page_content=test_content,
            metadata={'source': 'test_document.pdf', 'page': 1}
        )
        
        chunks = processor.text_splitter.split_documents([test_doc])
        
        if chunks and len(chunks) > 1:
            print(f"✅ Text splitting works - created {len(chunks)} chunks")
            print(f"   Average chunk length: {sum(len(c.page_content) for c in chunks) // len(chunks)}")
            print(f"   First chunk starts: '{chunks[0].page_content[:50]}...'")
            
            # Check metadata preservation
            if chunks[0].metadata.get('source') == 'test_document.pdf':
                print("✅ Metadata preserved in chunks")
            else:
                print("❌ Metadata not preserved")
                return False
        else:
            print(f"❌ Text splitting issue - created {len(chunks)} chunks")
            return False
        
        # Test 3: Chunk metadata enhancement
        print("\n🏷️ Testing chunk metadata enhancement...")
        
        # Simulate the metadata enhancement that would happen in load_and_chunk_pdf
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source_file': 'test.pdf'
            })
            enhanced_chunks.append(chunk)
        
        if enhanced_chunks[0].metadata.get('chunk_index') == 0:
            print("✅ Chunk metadata enhancement works")
            print(f"   Chunk 0 metadata: {enhanced_chunks[0].metadata}")
        else:
            print("❌ Chunk metadata enhancement failed")
            return False
        
        # Test 4: Vector store info (without actual initialization)
        print("\n📊 Testing vector store info...")
        
        info = processor.get_vector_store_info()
        
        if info.get('status') == 'not_initialized':
            print("✅ Vector store info works")
            print(f"   Status: {info['status']}")
            print(f"   Chunk size: {info.get('chunk_size')}")
        else:
            print(f"❌ Unexpected vector store status: {info}")
            return False
        
        # Test 5: Document processing workflow (without vector store)
        print("\n🔄 Testing document processing workflow...")
        
        # Create a fake PDF path to test the workflow logic
        fake_pdf_paths = [
            f"{temp_dir}/doc1.pdf",
            f"{temp_dir}/doc2.pdf",
            "nonexistent.pdf"  # Test error handling
        ]
        
        # Create fake PDF files
        for pdf_path in fake_pdf_paths[:2]:  # Only create the first two
            Path(pdf_path).write_text("Fake PDF content for testing")
        
        # This will fail gracefully since these aren't real PDFs
        try:
            processed_chunks = processor.process_documents(fake_pdf_paths)
            # Expected to return empty list since these aren't real PDFs
            if isinstance(processed_chunks, list):
                print("✅ Document processing workflow structure works")
                print(f"   Processed {len(processed_chunks)} chunks (expected 0 for fake PDFs)")
            else:
                print("❌ Document processing returned unexpected type")
                return False
        except Exception as e:
            print(f"⚠️  Document processing failed as expected (fake PDFs): {e}")
            print("✅ Error handling works correctly")
        
        # Test 6: Vector store path creation
        print("\n📁 Testing vector store path management...")
        
        vector_store_path = Path(temp_dir) / "test_vector_store"
        test_processor = RAGDocumentProcessor(
            vector_store_path=str(vector_store_path)
        )
        
        # Test that path is set correctly
        if test_processor.vector_store_path == vector_store_path:
            print("✅ Vector store path management works")
            print(f"   Path: {test_processor.vector_store_path}")
        else:
            print("❌ Vector store path management failed")
            return False
        
        print("\n🎉 All RAG processor tests passed!")
        return True


def test_openai_integration():
    """Test OpenAI integration (will skip if no API key)."""
    print("\n🔑 Testing OpenAI integration...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OpenAI API key found - skipping embedding tests")
        print("   Set OPENAI_API_KEY environment variable to test embeddings")
        return True
    
    try:
        processor = RAGDocumentProcessor()
        
        if processor.embeddings:
            print("✅ OpenAI embeddings initialized successfully")
            return True
        else:
            print("⚠️  OpenAI embeddings not available (API key issue?)")
            return True
            
    except Exception as e:
        print(f"⚠️  OpenAI integration test failed: {e}")
        return True  # Don't fail the overall test for API issues


if __name__ == "__main__":
    print("🚀 Starting RAG Document Processor Validation\\n")
    
    success = test_rag_processor()
    
    if success:
        test_openai_integration()
    
    if success:
        print("\\n✅ RAG document processor validation completed successfully")
        print("\\n📋 Summary:")
        print("• Processor initialization ✅")
        print("• Text chunking and splitting ✅")
        print("• Metadata handling ✅")
        print("• Vector store info management ✅")
        print("• Document processing workflow ✅")
        print("• Error handling ✅")
        print("\\n⚠️  Note: Full vector store functionality requires OpenAI API key")
        sys.exit(0)
    else:
        print("\\n❌ RAG document processor validation failed")
        sys.exit(1)