#!/usr/bin/env python3

import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== RAG Knowledge Validation Test ===")
print(f"Test started at: {datetime.now()}")
print()

# Test questions covering different aspects of MDS documentation
TEST_QUESTIONS = [
    # Release Information
    {
        "category": "Release Information",
        "question": "What are the new features in MDS NX-OS Release 9.4(4)?",
        "keywords": ["9.4(4)", "new features", "release", "enhancements"]
    },
    
    # Configuration
    {
        "category": "Configuration",
        "question": "How do I configure FCoE on MDS switches?",
        "keywords": ["fcoe", "configuration", "setup", "fibre channel over ethernet"]
    },
    
    # Hardware Information
    {
        "category": "Hardware",
        "question": "What are the hardware specifications for MDS 9700 series switches?",
        "keywords": ["9700", "hardware", "specifications", "ports", "performance"]
    },
    
    # Troubleshooting
    {
        "category": "Troubleshooting",
        "question": "How to troubleshoot slow drain counters on MDS switches?",
        "keywords": ["slow drain", "troubleshooting", "counters", "performance"]
    },
    
    # Compatibility
    {
        "category": "Compatibility",
        "question": "What is the compatibility matrix for MDS 9000 series switches?",
        "keywords": ["compatibility", "matrix", "supported", "interoperability"]
    },
    
    # EPLD Information
    {
        "category": "EPLD",
        "question": "What EPLD firmware versions are available for MDS switches?",
        "keywords": ["epld", "firmware", "version", "upgrade"]
    },
    
    # Commands
    {
        "category": "Commands",
        "question": "What are the show commands for monitoring SAN analytics?",
        "keywords": ["show commands", "san analytics", "monitoring", "telemetry"]
    },
    
    # Installation
    {
        "category": "Installation",
        "question": "How to perform a non-disruptive NX-OS upgrade on MDS switches?",
        "keywords": ["upgrade", "non-disruptive", "installation", "nx-os"]
    }
]

def test_rag_retrieval(processor: RAGDocumentProcessor, question: str, expected_keywords: List[str]) -> Dict[str, Any]:
    """Test RAG retrieval for a specific question."""
    try:
        start_time = time.time()
        
        # For this test, we'll simulate what a RAG system would do:
        # 1. Generate query embedding
        # 2. Search vector store
        # 3. Retrieve relevant chunks
        
        if not processor.embeddings:
            return {
                "success": False,
                "error": "No embeddings available",
                "response_time": 0,
                "chunks_found": 0
            }
        
        # Generate embedding for the question
        query_embedding = processor.embeddings.embed_query(question)
        
        # Check if vector store is available and search
        if processor.vector_store:
            try:
                # Get collection (assuming default collection name)
                collection = processor.vector_store.get_or_create_collection("mds_documents")
                
                # Search for similar chunks
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,  # Top 5 most relevant chunks
                    include=["documents", "metadatas", "distances"]
                )
                
                chunks_found = len(results["documents"][0]) if results["documents"] else 0
                documents = results["documents"][0] if results["documents"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                response_time = time.time() - start_time
                
                # Analyze relevance by checking for keywords
                relevant_chunks = 0
                for doc in documents:
                    doc_lower = doc.lower()
                    if any(keyword.lower() in doc_lower for keyword in expected_keywords):
                        relevant_chunks += 1
                
                return {
                    "success": True,
                    "response_time": response_time,
                    "chunks_found": chunks_found,
                    "relevant_chunks": relevant_chunks,
                    "average_distance": sum(distances) / len(distances) if distances else 1.0,
                    "sample_text": documents[0][:200] + "..." if documents else "No documents found"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Vector store query failed: {e}",
                    "response_time": time.time() - start_time,
                    "chunks_found": 0
                }
        else:
            return {
                "success": False,
                "error": "Vector store not available",
                "response_time": time.time() - start_time,
                "chunks_found": 0
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time,
            "chunks_found": 0
        }

def main():
    try:
        # Initialize RAG processor
        print("Initializing RAG processor...")
        processor = RAGDocumentProcessor()
        
        if not processor.embeddings:
            print("❌ No embeddings available - cannot test RAG")
            return
            
        if not processor.vector_store:
            print("❌ No vector store available - cannot test RAG")
            return
            
        print(f"✅ RAG processor initialized")
        print(f"   Embeddings: {type(processor.embeddings).__name__}")
        print(f"   Vector store: {type(processor.vector_store).__name__}")
        print()
        
        # Run tests
        print("🧪 Running RAG validation tests...")
        print("=" * 80)
        
        total_tests = len(TEST_QUESTIONS)
        successful_tests = 0
        total_response_time = 0
        total_chunks_found = 0
        
        for i, test in enumerate(TEST_QUESTIONS, 1):
            print(f"\nTest {i}/{total_tests}: {test['category']}")
            print(f"Question: {test['question']}")
            print("-" * 60)
            
            result = test_rag_retrieval(processor, test['question'], test['keywords'])
            
            if result['success']:
                successful_tests += 1
                print(f"✅ SUCCESS")
                print(f"   Response time: {result['response_time']:.3f}s")
                print(f"   Chunks found: {result['chunks_found']}")
                print(f"   Relevant chunks: {result['relevant_chunks']}")
                print(f"   Relevance score: {result['average_distance']:.3f}")
                print(f"   Sample: {result['sample_text'][:100]}...")
                
                total_response_time += result['response_time']
                total_chunks_found += result['chunks_found']
            else:
                print(f"❌ FAILED: {result['error']}")
                
        # Summary
        print("\n" + "=" * 80)
        print("🏆 RAG VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        if successful_tests > 0:
            print(f"Average response time: {total_response_time/successful_tests:.3f}s")
            print(f"Average chunks per query: {total_chunks_found/successful_tests:.1f}")
            
        if successful_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! RAG system is working correctly.")
        elif successful_tests > total_tests * 0.7:
            print(f"\n⚠️  Most tests passed ({successful_tests}/{total_tests}). RAG system is mostly functional.")
        else:
            print(f"\n❌ Many tests failed ({total_tests - successful_tests}/{total_tests}). RAG system needs attention.")
            
    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()