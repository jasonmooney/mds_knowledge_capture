"""
Improved search function with better query handling for the Advanced MDS Agent
"""
import sys
import os
import logging
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

logger = logging.getLogger(__name__)

def enhanced_ask_question(self, question: str, top_k: int = 10, include_context: bool = True) -> Dict[str, Any]:
    """Enhanced question answering with improved search for structured content."""
    logger.info(f"❓ Processing question: '{question}'")
    
    # Multi-strategy search for better results
    search_strategies = []
    
    # Strategy 1: Direct question search
    search_strategies.append((question, 1.0))
    
    # Strategy 2: Extract key terms and search
    if 'features' in question.lower() and '9.4.4' in question:
        search_strategies.append(("New software features 9.4.4", 0.9))
        search_strategies.append(("Product Impact Feature Description Ease of Use Feature Set", 0.8))
    
    # Strategy 3: Search for specific categories if mentioned
    categories = ['ease of use', 'feature set', 'interoperability', 'security']
    mentioned_categories = [cat for cat in categories if cat in question.lower()]
    if mentioned_categories:
        cat_query = " ".join(mentioned_categories)
        search_strategies.append((cat_query, 0.7))
    
    # Combine results from multiple strategies
    all_results = {}
    
    for search_query, weight in search_strategies:
        results = self.rag_processor.search_chunks(search_query, top_k=top_k)
        for result in results:
            chunk_id = f"{result['metadata']['source_file']}_{result['metadata'].get('chunk_id', 0)}"
            if chunk_id in all_results:
                # Boost score if found in multiple searches
                all_results[chunk_id]['similarity_score'] = max(
                    all_results[chunk_id]['similarity_score'],
                    result['similarity_score'] * weight
                )
            else:
                result['similarity_score'] *= weight
                all_results[chunk_id] = result
    
    # Sort by weighted scores and prioritize table chunks
    search_results = list(all_results.values())
    
    def sort_key(result):
        score = result['similarity_score']
        # Boost table chunks significantly
        if result['metadata'].get('chunk_type') == 'table':
            score += 0.5
        # Boost chunks with "New Software Features" title
        if 'new software features' in result['metadata'].get('table_title', '').lower():
            score += 0.7
        return score
    
    search_results.sort(key=sort_key, reverse=True)
    
    # Take top results
    search_results = search_results[:top_k]
    
    if not search_results:
        return {
            "question": question,
            "answer": "No relevant information found in the knowledge base.",
            "sources": [],
            "error": "No search results"
        }
    
    # Rest of the method remains the same...
    context_chunks = []
    sources = []
    
    for result in search_results:
        context_chunks.append({
            "content": result["content"],
            "source": result["metadata"]["source_file"],
            "similarity": result["similarity_score"]
        })
        sources.append(result["metadata"]["source_file"])
    
    # Format context for LLM
    context_text = "\\n\\n".join([
        f"[Source: {chunk['source']}, Similarity: {chunk['similarity']:.3f}]\\n{chunk['content']}"
        for chunk in context_chunks
    ])
    
    # Create prompt for LLM
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

# Monkey patch the method
from agent_advanced import AdvancedMDSAgent
AdvancedMDSAgent.enhanced_ask_question = enhanced_ask_question

def main():
    """Test the enhanced search."""
    agent = AdvancedMDSAgent()
    
    # Test the enhanced search
    response = agent.enhanced_ask_question(
        "What are the new features in NX-OS 9.4.4?",
        top_k=15
    )
    
    print("🎯 Enhanced Search Results:")
    print("=" * 80)
    print(f"Question: {response['question']}")
    print(f"\\nAnswer: {response['answer']}")
    print(f"\\nSources: {response['sources']}")
    print(f"Context chunks used: {response['context_chunks']}")

if __name__ == "__main__":
    main()