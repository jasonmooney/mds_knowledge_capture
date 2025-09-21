#!/usr/bin/env python3
"""
Test script to demonstrate MDS Knowledge Capture Agent 
processing the Cisco MDS 9000 documentation hierarchy WITHOUT OpenAI API.

This shows the document discovery, classification, and metadata management
capabilities using the provided URL hierarchy.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from scraper import MDSDocumentScraper
from metadata import MetadataManager
from revision_control import RevisionController


async def analyze_cisco_hierarchy():
    """Analyze the Cisco MDS hierarchy without OpenAI API requirements."""
    
    print("🚀 MDS Knowledge Capture - Cisco Hierarchy Analysis")
    print("=" * 60)
    
    # The example hierarchy you provided
    root_url = "https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html"
    
    # Simulate discovered URLs from the hierarchy
    discovered_urls = [
        "https://www.cisco.com/c/en/us/td/docs/dcn/mds9000/sw/9x/release-notes/cisco-mds-9000-nx-os-release-notes-944.html",
        "https://www.cisco.com/c/en/us/td/docs/dcn/mds9000/sw/9x/release-notes/transceivers/cisco-mds-9000-series-transceivers-release-notes-944.html", 
        "https://www.cisco.com/c/en/us/td/docs/switches/datacenter/mds9000/sw/b_MDS_NX-OS_Recommended_Releases.html",
        "https://www.cisco.com/c/en/us/td/docs/dcn/mds9000/sw/9x/command/cisco-mds-9000-nx-os-command-reference-guide-9x.html"
    ]
    
    # Corresponding PDF URLs
    pdf_urls = [url.replace('.html', '.pdf') for url in discovered_urls]
    
    print(f"📋 Root URL: {root_url}")
    print(f"🔍 Discovered {len(discovered_urls)} child HTML pages")
    print(f"📄 Corresponding {len(pdf_urls)} PDF documents")
    print()
    
    # Initialize components
    scraper = MDSDocumentScraper()
    metadata_manager = MetadataManager()
    revision_controller = RevisionController()
    
    print("📊 DOCUMENT ANALYSIS:")
    print("-" * 40)
    
    # Analyze each URL
    for i, (html_url, pdf_url) in enumerate(zip(discovered_urls, pdf_urls), 1):
        print(f"\n{i}. {html_url.split('/')[-1]}")
        
        # Extract document information
        doc_info = scraper.extract_document_info(html_url)
        
        print(f"   📄 PDF: {pdf_url.split('/')[-1]}")
        print(f"   🏷️  Title: {doc_info['title']}")
        print(f"   📁 Category: {doc_info['category']}")
        print(f"   🔢 Version: {doc_info['version']}")
        print(f"   📅 Date: {doc_info['date']}")
        
        # Simulate metadata storage
        try:
            doc_id = metadata_manager.add_document(
                url=pdf_url,
                title=doc_info['title'],
                file_path=f"knowledge_source/current/{pdf_url.split('/')[-1]}",
                file_hash="simulated_hash_" + str(i),
                category=doc_info['category'],
                version=doc_info['version']
            )
            print(f"   ✅ Metadata stored (ID: {doc_id})")
        except Exception as e:
            print(f"   ⚠️  Metadata error: {e}")
    
    print("\n" + "=" * 60)
    print("📈 HIERARCHY SUMMARY:")
    print("-" * 30)
    
    # Categorize documents
    categories = {}
    versions = set()
    
    for url in discovered_urls:
        if 'release-notes' in url and 'transceivers' in url:
            category = 'Transceiver Release Notes'
        elif 'release-notes' in url:
            category = 'System Release Notes'
        elif 'command' in url:
            category = 'Command Reference'
        elif 'Recommended_Releases' in url:
            category = 'Recommended Releases'
        else:
            category = 'Other'
            
        categories[category] = categories.get(category, 0) + 1
        
        # Extract version info
        if '944' in url:
            versions.add('9.4.4')
        elif '9x' in url:
            versions.add('9.x')
    
    print(f"🎯 Product Line: MDS 9000 Series")
    print(f"🏷️  Platform: NX-OS")
    print(f"📦 Versions Found: {', '.join(sorted(versions))}")
    print(f"📁 Document Categories:")
    for category, count in categories.items():
        print(f"   • {category}: {count} document(s)")
    
    print(f"\n💾 Total Documents in Database: {len(metadata_manager.get_all_documents())}")
    
    # Show some example queries
    print("\n" + "=" * 60)
    print("🔍 EXAMPLE QUERIES:")
    print("-" * 25)
    
    all_docs = metadata_manager.get_all_documents()
    
    # Find release notes
    release_notes = [doc for doc in all_docs if 'release' in doc['category'].lower()]
    print(f"📋 Release Notes: {len(release_notes)} documents")
    
    # Find command references  
    command_docs = [doc for doc in all_docs if 'command' in doc['category'].lower()]
    print(f"⚙️  Command References: {len(command_docs)} documents")
    
    # Find version 9.4.4 docs
    v944_docs = [doc for doc in all_docs if '944' in doc['version']]
    print(f"🔢 Version 9.4.4 Docs: {len(v944_docs)} documents")
    
    print("\n✅ Hierarchy analysis complete!")
    print("This demonstrates how our agent would:")
    print("  • Discover document hierarchies")
    print("  • Extract metadata and categorization") 
    print("  • Store structured information")
    print("  • Enable semantic search and retrieval")


if __name__ == "__main__":
    print("🤖 MDS Knowledge Capture - Cisco Hierarchy Demo")
    print("Analyzing the provided URL hierarchy without OpenAI API")
    print()
    
    # Run the analysis
    asyncio.run(analyze_cisco_hierarchy())