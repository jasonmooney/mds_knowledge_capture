"""
Advanced MDS Knowledge Capture Agent with Full RAG Support
This version integrates the enhanced RAG processor with ChromaDB vector search
for intelligent document analysis and question answering.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import argparse

from agent import MDSKnowledgeCaptureAgent  # Original agent
from rag_enhanced import EnhancedRAGProcessor  # New RAG processor

logger = logging.getLogger(__name__)


class AdvancedMDSAgent:
    """Advanced MDS Knowledge Capture Agent with full RAG support."""
    
    def __init__(self, config_file: str = "config/agent_config.json"):
        """Initialize the advanced agent with RAG capabilities."""
        self.config_file = config_file
        
        # Load configuration
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "knowledge_source": {
                    "urls": [
                        "https://www.cisco.com/c/en/us/support/storage-networking/mds-9000-series-multilayer-switches/products-release-notes-list.html",
                        "https://www.cisco.com/c/en/us/support/storage-networking/mds-9000-series-multilayer-switches/products-command-reference-list.html"
                    ],
                    "current_dir": "knowledge_source/current",
                    "archive_dir": "knowledge_source/archive"
                },
                "llm": {
                    "provider": "openrouter",
                    "model": "mistralai/mistral-7b-instruct",
                    "api_key_env": "OPENROUTER_API_KEY"
                },
                "rag": {
                    "vector_store_path": "chroma_db",
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "collection_name": "mds_documents",
                    "embedding_model": "all-MiniLM-L6-v2"
                }
            }
        
        # Initialize original agent
        self.base_agent = MDSKnowledgeCaptureAgent()
        
        # Initialize enhanced RAG processor
        self.rag_processor = EnhancedRAGProcessor(
            vector_store_path=self.config["rag"]["vector_store_path"],
            chunk_size=self.config["rag"]["chunk_size"],
            chunk_overlap=self.config["rag"]["chunk_overlap"],
            collection_name=self.config["rag"]["collection_name"],
            embedding_model=self.config["rag"]["embedding_model"]
        )
        
        logger.info("✅ Advanced MDS Agent initialized with full RAG support")
        
    def run_complete_cycle(self) -> Dict[str, Any]:
        """Run a complete knowledge capture and RAG processing cycle."""
        logger.info("🚀 Starting complete knowledge capture and RAG processing cycle...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "web_scraping": {},
            "rag_processing": {},
            "vector_search_ready": False,
            "errors": []
        }
        
        try:
            # Step 1: Run original agent for web scraping and document collection
            logger.info("📡 Phase 1: Web scraping and document collection...")
            scrape_results = self.base_agent.run()
            results["web_scraping"] = scrape_results
            
            # Step 2: Process documents with enhanced RAG
            logger.info("🧠 Phase 2: Enhanced RAG processing with vector embeddings...")
            rag_results = self.rag_processor.process_current_documents()
            results["rag_processing"] = rag_results
            
            # Check if vector search is ready
            if rag_results["vector_store_chunks"] > 0:
                results["vector_search_ready"] = True
                logger.info("✅ Vector search capabilities ready!")
            else:
                results["errors"].append("Vector store is empty - no semantic search available")
                logger.warning("⚠️  Vector store is empty")
            
            # Step 3: Get comprehensive statistics
            rag_stats = self.rag_processor.get_stats()
            results["rag_stats"] = rag_stats
            
            logger.info("🎉 Complete cycle finished successfully!")
            
        except Exception as e:
            error_msg = f"Error in complete cycle: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def ask_question(self, question: str, top_k: int = 5, include_context: bool = True) -> Dict[str, Any]:
        """Ask a question using semantic search and LLM analysis with enhanced table prioritization."""
        logger.info(f"❓ Processing question: '{question}'")
        
        # Multi-strategy search for better table content discovery
        all_results = {}
        
        # Strategy 1: Direct question search
        search_results = self.rag_processor.search_chunks(question, top_k=top_k * 3)
        for result in search_results:
            chunk_id = f"{result['metadata']['source_file']}_{result['metadata'].get('chunk_id', 0)}"
            all_results[chunk_id] = result
        
        # Strategy 2: If asking about features, search for feature-specific terms
        if 'features' in question.lower() and '9.4.4' in question:
            feature_queries = [
                "New software features",
                "Ease of Use Feature Set Interoperability Security",
                "Product Impact Feature Description",
                "Fabric Congestion Diagnostics SMA FPIN RFC AES-256"
            ]
            
            for query in feature_queries:
                results = self.rag_processor.search_chunks(query, top_k=top_k * 2)
                for result in results:
                    chunk_id = f"{result['metadata']['source_file']}_{result['metadata'].get('chunk_id', 0)}"
                    if chunk_id not in all_results:
                        all_results[chunk_id] = result
        
        # Convert back to list and apply enhanced sorting
        search_results = list(all_results.values())
        
        def enhanced_sort_key(result):
            score = result['similarity_score']
            metadata = result['metadata']
            content = result['content'].lower()
            
            # Major boost for table chunks
            if metadata.get('chunk_type') == 'table':
                score += 1.0
                
            # Huge boost for "New Software Features" tables
            if 'new software features' in metadata.get('table_title', '').lower():
                score += 2.0
                
            # Boost for content containing all key feature terms
            feature_terms = ['ease of use', 'feature set', 'interoperability', 'security']
            term_count = sum(1 for term in feature_terms if term in content)
            score += term_count * 0.3
            
            # Boost for 9.4.4 specific content
            if '9.4.4' in content or '9.4(4)' in content:
                score += 0.5
                
            return score
        
        # Sort with enhanced scoring and take top results
        search_results.sort(key=enhanced_sort_key, reverse=True)
        search_results = search_results[:top_k]
        
        if not search_results:
            return {
                "question": question,
                "answer": "No relevant information found in the knowledge base.",
                "sources": [],
                "error": "No search results"
            }
        
        # Prepare context for LLM
        context_chunks = []
        sources = []
        
        for result in search_results:
            context_chunks.append({
                "content": result["content"],
                "source": result["metadata"]["source_file"],
                "similarity": enhanced_sort_key(result)  # Use enhanced score
            })
            sources.append(result["metadata"]["source_file"])
        
        # Format context for LLM with clear structure
        context_text = "\\n\\n".join([
            f"[Source: {chunk['source']}, Relevance: {chunk['similarity']:.3f}]\\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
        # Enhanced prompt for feature questions
        if 'features' in question.lower() and '9.4.4' in question:
            prompt = f"""Based on the following context from Cisco MDS documentation, please provide a comprehensive answer about the new features in NX-OS 9.4.4.

IMPORTANT: Look for table content that lists features by categories like "Ease of Use", "Feature Set", "Interoperability", and "Security". This information may be formatted as a table with columns like "Product Impact", "Feature", and "Description".

Context:
{context_text}

Question: {question}

Please organize your answer by the feature categories found in the context (Ease of Use, Feature Set, Interoperability, Security) and list the specific features and their descriptions under each category.

Answer:"""
        else:
            # Standard prompt for other questions
            prompt = f"""Based on the following context from Cisco MDS documentation, please answer the question accurately and concisely.
        
Context:
{context_text}

Question: {question}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain sufficient information to answer the question completely, please indicate what additional information might be needed.

Answer:"""
        
        try:
            # Use the base agent's LLM for analysis
            if hasattr(self.base_agent, 'llm') and self.base_agent.llm:
                llm_response = self.base_agent.llm.invoke(prompt)
                answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            else:
                answer = "LLM not available for analysis. Here's the most relevant context found:\\n\\n" + context_text[:1000] + "..."
            
            return {
                "question": question,
                "answer": answer,
                "sources": list(set(sources)),
                "context_chunks": len(search_results),
                "search_results": search_results if include_context else []
            }
            
        except Exception as e:
            logger.error(f"Error processing question with LLM: {e}")
            return {
                "question": question,
                "answer": f"Error processing with LLM: {str(e)}. Here's the relevant context:\\n\\n{context_text[:1000]}",
                "sources": list(set(sources)),
                "error": str(e)
            }
    
    def interactive_mode(self):
        """Run in interactive question-answering mode."""
        print("\\n🤖 Advanced MDS Knowledge Agent - Interactive Mode")
        print("=" * 60)
        print("Ask questions about Cisco MDS documentation!")
        print("Type 'exit' to quit, 'stats' for statistics, 'refresh' to update documents.\\n")
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif question.lower() == 'stats':
                    stats = self.rag_processor.get_stats()
                    print(f"\\n📊 Knowledge Base Statistics:")
                    print(f"   • Total vectors: {stats.get('total_vectors', 'N/A')}")
                    print(f"   • Unique files: {stats.get('unique_files', 'N/A')}")
                    print(f"   • Vector store available: {stats['vector_store_available']}")
                    print(f"   • Embedding model: {stats['embedding_model']}")
                    continue
                elif question.lower() == 'refresh':
                    print("🔄 Refreshing knowledge base...")
                    results = self.run_complete_cycle()
                    print(f"✅ Processed {results['rag_processing'].get('total_chunks', 0)} chunks")
                    continue
                elif not question:
                    continue
                
                # Process the question
                print("🔍 Searching knowledge base...")
                response = self.ask_question(question)
                
                print(f"\\n💡 Answer:")
                print(f"{response['answer']}")
                
                if response.get('sources'):
                    print(f"\\n📚 Sources: {', '.join(response['sources'])}")
                
                print("\\n" + "-" * 60)
                
            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                continue


def main():
    """Main entry point for the advanced MDS agent."""
    parser = argparse.ArgumentParser(description="Advanced MDS Knowledge Capture Agent with RAG")
    parser.add_argument("--mode", choices=["cycle", "interactive", "question"], default="cycle",
                       help="Mode to run: complete cycle, interactive, or single question")
    parser.add_argument("--question", type=str, help="Single question to ask (for question mode)")
    parser.add_argument("--config", type=str, default="config/agent_config.json",
                       help="Configuration file path")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize agent
    agent = AdvancedMDSAgent(config_file=args.config)
    
    if args.mode == "cycle":
        # Run complete cycle
        results = agent.run_complete_cycle()
        
        print("\\n🎯 Complete Cycle Results:")
        print("=" * 50)
        print(f"📡 Web scraping: {len(results['web_scraping'].get('processed_urls', []))} URLs processed")
        print(f"📄 Documents: {results['rag_processing'].get('total_chunks', 0)} chunks created")
        print(f"🗄️  Vector store: {results['rag_processing'].get('vector_store_chunks', 0)} embeddings")
        print(f"🔍 Search ready: {results['vector_search_ready']}")
        print(f"⏱️  Processing time: {results['rag_processing'].get('processing_time', 'N/A')}")
        
        if results['errors']:
            print(f"\\n❌ Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"   • {error}")
    
    elif args.mode == "interactive":
        # Run interactive mode
        agent.interactive_mode()
    
    elif args.mode == "question":
        if not args.question:
            print("❌ Error: --question required for question mode")
            return
        
        # Process single question
        response = agent.ask_question(args.question)
        print(f"\\n❓ Question: {response['question']}")
        print(f"💡 Answer: {response['answer']}")
        
        if response.get('sources'):
            print(f"📚 Sources: {', '.join(response['sources'])}")


if __name__ == "__main__":
    main()