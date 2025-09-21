#!/usr/bin/env python3
"""
Test script to demonstrate MDS Knowledge Capture Agent 
processing the Cisco MDS 9000 documentation hierarchy.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from agent import MDSKnowledgeCaptureAgent
from metadata import MetadataManager


async def test_cisco_hierarchy():
    """Test the agent with the provided Cisco MDS hierarchy."""
    
    print("🚀 MDS Knowledge Capture Agent - Cisco Hierarchy Test")
    print("=" * 60)
    
    # Initialize components
    agent = MDSKnowledgeCaptureAgent()
    metadata_manager = MetadataManager()
    
    # The example hierarchy you provided
    test_urls = [
        "https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html"
    ]
    
    print(f"📋 Starting with {len(test_urls)} root URL(s):")
    for url in test_urls:
        print(f"  🔗 {url}")
    
    print("\n" + "=" * 60)
    
    # Test the agent workflow
    try:
        # Create initial state
        initial_state = {
            "urls": test_urls,
            "analysis_results": [],
            "scraped_data": [],
            "downloaded_files": [],
            "processed_revisions": []
        }
        
        print("🔍 STEP 1: Analyzing URLs...")
        result_1 = await agent.analyze_urls(initial_state)
        
        print(f"✅ Analysis complete. Found {len(result_1.get('analysis_results', []))} results")
        for result in result_1.get('analysis_results', [])[:3]:  # Show first 3
            print(f"   📊 {result}")
        
        print("\n🕷️  STEP 2: Scraping documents...")
        result_2 = await agent.scrape_documents(result_1)
        
        scraped_count = len(result_2.get('scraped_data', []))
        print(f"✅ Scraping complete. Scraped {scraped_count} pages")
        
        print("\n📥 STEP 3: Downloading PDFs...")
        result_3 = await agent.download_documents(result_2)
        
        download_count = len(result_3.get('downloaded_files', []))
        print(f"✅ Download simulation complete. Would download {download_count} files")
        
        print("\n🔄 STEP 4: Processing revisions...")
        final_result = await agent.process_revisions(result_3)
        
        revision_count = len(final_result.get('processed_revisions', []))
        print(f"✅ Revision processing complete. Processed {revision_count} revisions")
        
        print("\n" + "=" * 60)
        print("📈 FINAL RESULTS:")
        print(f"  🔗 URLs analyzed: {len(final_result.get('urls', []))}")
        print(f"  📊 Analysis results: {len(final_result.get('analysis_results', []))}")
        print(f"  🕷️  Scraped pages: {len(final_result.get('scraped_data', []))}")
        print(f"  📥 Downloaded files: {len(final_result.get('downloaded_files', []))}")
        print(f"  🔄 Processed revisions: {len(final_result.get('processed_revisions', []))}")
        
        # Show some metadata examples
        print("\n📋 Sample Document Metadata:")
        try:
            docs = metadata_manager.get_all_documents()
            if docs:
                for doc in docs[:3]:  # Show first 3 documents
                    print(f"  📄 {doc['title'][:50]}...")
                    print(f"     🔗 URL: {doc['url']}")
                    print(f"     📅 Last Updated: {doc['last_updated']}")
                    print()
            else:
                print("  ℹ️  No documents in database yet (test mode)")
        except Exception as e:
            print(f"  ⚠️  Metadata query error: {e}")
        
    except Exception as e:
        print(f"❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤖 Testing MDS Knowledge Capture Agent with Cisco Hierarchy")
    print("This demonstrates how the agent would process the provided URLs")
    print()
    
    # Run the test
    asyncio.run(test_cisco_hierarchy())