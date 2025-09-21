#!/usr/bin/env python3

import sys
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Intelligent RAG Validation with OpenRouter ===")
print("Using AI to evaluate if retrieved content answers questions")
print()

def get_openrouter_response(prompt: str) -> str:
    """Get response from OpenRouter AI to evaluate RAG results."""
    try:
        import openai
        
        # Configure OpenAI client for OpenRouter
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            return "❌ No OpenRouter API key found"
        
        client = openai.OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        response = client.chat.completions.create(
            model="microsoft/wizardlm-2-8x22b",  # Good reasoning model
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert technical documentation analyst specializing in Cisco MDS switches and storage networking. Evaluate if retrieved text chunks answer user questions accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "No response content"
        
    except Exception as e:
        return f"❌ OpenRouter error: {e}"

def evaluate_rag_response(question: str, retrieved_texts: List[str], max_texts: int = 3) -> Dict[str, Any]:
    """Evaluate if retrieved texts answer the question using OpenRouter AI."""
    
    if not retrieved_texts:
        return {
            "has_answer": False,
            "confidence": 0.0,
            "explanation": "No documents retrieved",
            "answer": "No information found"
        }
    
    # Limit texts to avoid token limits
    texts_to_evaluate = retrieved_texts[:max_texts]
    
    # Create evaluation prompt
    prompt = f"""
QUESTION: {question}

RETRIEVED TEXT CHUNKS:
{'-' * 50}
"""
    
    for i, text in enumerate(texts_to_evaluate, 1):
        # Clean and truncate text
        clean_text = text.replace('\n', ' ').replace('\t', ' ').strip()[:800]
        prompt += f"\nChunk {i}:\n{clean_text}\n{'-' * 30}\n"
    
    prompt += f"""
EVALUATION TASK:
1. Does the retrieved content contain information that answers the question?
2. Provide a confidence score (0.0 to 1.0) for how well it answers the question
3. Extract the specific answer from the content (if available)
4. Explain why it does or doesn't answer the question

Please respond in this JSON format:
{{
    "has_answer": true/false,
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of evaluation",
    "answer": "extracted answer or 'No clear answer found'"
}}
"""
    
    # Get AI evaluation
    ai_response = get_openrouter_response(prompt)
    
    try:
        # Try to parse JSON response
        if ai_response.startswith("❌"):
            return {
                "has_answer": False,
                "confidence": 0.0,
                "explanation": ai_response,
                "answer": "AI evaluation failed"
            }
        
        # Extract JSON from response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            evaluation = json.loads(json_str)
            
            # Ensure all required fields
            return {
                "has_answer": evaluation.get("has_answer", False),
                "confidence": float(evaluation.get("confidence", 0.0)),
                "explanation": evaluation.get("explanation", "No explanation"),
                "answer": evaluation.get("answer", "No answer extracted")
            }
        else:
            return {
                "has_answer": False,
                "confidence": 0.0,
                "explanation": "Could not parse AI response",
                "answer": ai_response
            }
            
    except Exception as e:
        return {
            "has_answer": False,
            "confidence": 0.0,
            "explanation": f"JSON parsing error: {e}",
            "answer": ai_response
        }

def run_intelligent_rag_validation():
    """Run comprehensive RAG validation with AI evaluation."""
    
    try:
        processor = RAGDocumentProcessor()
        
        if not processor.vector_store or not processor.embeddings:
            print("❌ Vector store or embeddings not available")
            return
        
        # Use the test collection
        collection = processor.vector_store.get_or_create_collection("mds_test")
        count = collection.count()
        
        print(f"✅ Using collection 'mds_test' with {count} documents")
        
        if count == 0:
            print("❌ Test collection is empty - run max_gpu_test.py first")
            return
        
        # Comprehensive test questions
        test_questions = [
            {
                "category": "Software Releases",
                "question": "What are the recommended software releases for Cisco MDS 9000 switches?",
                "expected_keywords": ["recommended", "release", "software", "version"]
            },
            {
                "category": "Configuration",
                "question": "How do I configure FCoE (Fibre Channel over Ethernet) on MDS switches?",
                "expected_keywords": ["fcoe", "configure", "fibre channel", "ethernet"]
            },
            {
                "category": "Hardware Compatibility",
                "question": "What are the compatibility requirements and supported modules for MDS 9000 series?",
                "expected_keywords": ["compatibility", "modules", "supported", "requirements"]
            },
            {
                "category": "Commands",
                "question": "What show commands are available for monitoring MDS switch status?",
                "expected_keywords": ["show", "commands", "monitoring", "status"]
            },
            {
                "category": "Troubleshooting",
                "question": "How to troubleshoot slow drain issues on MDS switches?",
                "expected_keywords": ["slow drain", "troubleshoot", "issues", "performance"]
            }
        ]
        
        print(f"\n🧪 Running intelligent RAG validation with {len(test_questions)} questions")
        print("=" * 70)
        
        total_tests = len(test_questions)
        successful_answers = 0
        high_confidence_answers = 0
        
        for i, test_case in enumerate(test_questions, 1):
            question = test_case["question"]
            category = test_case["category"]
            
            print(f"\nTest {i}/{total_tests}: {category}")
            print(f"Q: {question}")
            print("-" * 60)
            
            # Retrieve relevant documents
            query_embedding = processor.embeddings.embed_query(question)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["documents", "distances"]
            )
            
            if results and results["documents"] and results["documents"][0]:
                retrieved_texts = results["documents"][0]
                distances = results["distances"][0] if results.get("distances") and results["distances"] else []
                
                print(f"📄 Retrieved {len(retrieved_texts)} documents")
                
                # Evaluate with AI
                print("🤖 Evaluating with AI...")
                evaluation = evaluate_rag_response(question, retrieved_texts)
                
                # Display results
                if evaluation["has_answer"]:
                    print("✅ ANSWER FOUND")
                    successful_answers += 1
                    
                    if evaluation["confidence"] >= 0.7:
                        print("🔥 HIGH CONFIDENCE")
                        high_confidence_answers += 1
                    elif evaluation["confidence"] >= 0.4:
                        print("⚡ MEDIUM CONFIDENCE")
                    else:
                        print("⚠️  LOW CONFIDENCE")
                else:
                    print("❌ NO CLEAR ANSWER")
                
                print(f"   Confidence: {evaluation['confidence']:.2f}")
                print(f"   Explanation: {evaluation['explanation']}")
                print(f"   Answer: {evaluation['answer'][:200]}...")
                
            else:
                print("❌ No documents retrieved")
                evaluation = {
                    "has_answer": False,
                    "confidence": 0.0,
                    "explanation": "No documents found",
                    "answer": "No information available"
                }
        
        # Final summary
        print("\n" + "=" * 70)
        print("🏆 INTELLIGENT RAG VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Total questions tested: {total_tests}")
        print(f"Questions with answers: {successful_answers}")
        print(f"High confidence answers: {high_confidence_answers}")
        print(f"Answer success rate: {successful_answers/total_tests*100:.1f}%")
        print(f"High confidence rate: {high_confidence_answers/total_tests*100:.1f}%")
        
        if successful_answers >= total_tests * 0.8:
            print("\n🎉 EXCELLENT! RAG system provides good answers to most questions")
        elif successful_answers >= total_tests * 0.5:
            print("\n👍 GOOD! RAG system answers many questions but could be improved")
        else:
            print("\n⚠️  RAG system needs improvement - few questions answered well")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_intelligent_rag_validation()