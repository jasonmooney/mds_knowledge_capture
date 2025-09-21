#!/usr/bin/env python3

import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.rag_prep import RAGDocumentProcessor

print("=== Broader RAG Search: MDS 9.4.x Release Information ===")
print()

def search_version_info():
    """Search for any MDS version information in the dataset."""
    
    try:
        processor = RAGDocumentProcessor()
        
        if not processor.vector_store or not processor.embeddings:
            print("❌ Vector store or embeddings not available")
            return
        
        collection = processor.vector_store.get_or_create_collection("mds_test")
        count = collection.count()
        
        print(f"✅ Using collection 'mds_test' with {count} documents")
        
        # Broader version searches
        version_queries = [
            "MDS 9.4 release features",
            "NX-OS version 9.4",
            "Cisco MDS software version 9.4",
            "what's new in MDS 9.4"
        ]
        
        print(f"🔍 Searching for MDS 9.4.x information...")
        print("=" * 60)
        
        found_version_info = False
        
        for i, query in enumerate(version_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 40)
            
            query_embedding = processor.embeddings.embed_query(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=2,
                include=["documents", "distances", "metadatas"]
            )
            
            if results and results["documents"] and results["documents"][0]:
                retrieved_texts = results["documents"][0]
                distances = results["distances"][0] if results.get("distances") and results["distances"] else []
                
                for j, (text, distance) in enumerate(zip(retrieved_texts, distances), 1):
                    similarity = 1 - distance
                    
                    # Look for any version numbers
                    version_found = False
                    for version_pattern in ["9.4", "8.4", "6.2", "9.2", "9.3"]:
                        if version_pattern in text:
                            version_found = True
                            print(f"📍 Document {j} (similarity: {similarity:.3f}) - Contains {version_pattern}")
                            found_version_info = True
                            break
                    
                    if not version_found:
                        print(f"📄 Document {j} (similarity: {similarity:.3f}) - General content")
                    
                    # Show relevant excerpts
                    clean_text = text.replace('\n', ' ').replace('\t', ' ').strip()
                    
                    # Look for version-related content
                    version_keywords = ["release", "version", "9.4", "8.4", "6.2", "software", "NX-OS"]
                    relevant_sections = []
                    
                    for keyword in version_keywords:
                        if keyword.lower() in clean_text.lower():
                            # Find context around the keyword
                            idx = clean_text.lower().find(keyword.lower())
                            if idx != -1:
                                start = max(0, idx - 100)
                                end = min(len(clean_text), idx + 200)
                                section = clean_text[start:end].strip()
                                if section not in relevant_sections:
                                    relevant_sections.append(section)
                    
                    if relevant_sections:
                        print(f"   Relevant content: ...{relevant_sections[0]}...")
                    else:
                        # Show first part of content
                        preview = clean_text[:150] + "..." if len(clean_text) > 150 else clean_text
                        print(f"   Content: {preview}")
        
        print("\n" + "=" * 60)
        print("🔍 VERSION SEARCH SUMMARY")
        print("=" * 60)
        
        if found_version_info:
            print("✅ Found some MDS version information in the dataset")
            print("📝 The documents contain general release and version references")
            print("⚠️  However, no specific MDS 9.4.4 features were found")
            print("\n💡 Possible reasons:")
            print("   - The test dataset (128 docs) may not include 9.4.4 release notes")
            print("   - 9.4.4 information might be in the full dataset (9,971 docs)")
            print("   - The chunking may have split 9.4.4 feature information")
        else:
            print("❌ No specific version information found in current test dataset")
            print("💡 The test dataset may focus on general compatibility/recommendations")
        
        print(f"\n🎯 RECOMMENDATION:")
        print(f"   To find MDS 9.4.4 features, you may need to:")
        print(f"   1. Process the full document dataset (not just test subset)")
        print(f"   2. Look for specific 9.4.4 release notes documents")
        print(f"   3. Search for 'new features' or 'enhancements' in 9.4.4 context")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_version_info()