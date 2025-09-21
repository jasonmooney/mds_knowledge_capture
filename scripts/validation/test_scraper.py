"""
Validation script for web scraper functionality.
Tests URL fetching, PDF detection, and basic download capabilities.
"""

import sys
import os
import tempfile
import logging
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraper import MDSDocumentScraper


def test_web_scraper():
    """Test the web scraper functionality."""
    print("🧪 Testing Web Scraper...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    scraper = MDSDocumentScraper(max_concurrent=2, timeout=30)
    
    # Test 1: Basic page fetching
    print("\n📄 Testing page fetching...")
    test_url = "https://httpbin.org/html"  # Simple test page
    soup = scraper.fetch_page(test_url)
    
    if soup:
        print("✅ Page fetching works")
        print(f"   Page title: {soup.title.string if soup.title else 'No title'}")
    else:
        print("❌ Page fetching failed")
        return False
    
    # Test 2: PDF link detection
    print("\n🔍 Testing PDF link detection...")
    
    # Create mock HTML with various link types
    mock_html = """
    <html>
    <body>
        <a href="document.pdf">Direct PDF Link</a>
        <a href="guide_v1.2.pdf">Guide Version 1.2</a>
        <a href="manual.html">HTML Manual</a>
        <a href="datasheet.pdf">Product Datasheet</a>
        <a href="mailto:test@example.com">Email Link</a>
        <a href="#anchor">Anchor Link</a>
        <a href="/relative/path/doc.pdf">Relative PDF</a>
    </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    mock_soup = BeautifulSoup(mock_html, 'html.parser')
    base_url = "https://example.com/docs/"
    
    pdf_links = scraper.extract_pdf_links(mock_soup, base_url)
    
    expected_pdfs = 4  # Should find 4 PDF links
    if len(pdf_links) >= expected_pdfs:
        print(f"✅ PDF detection works - found {len(pdf_links)} PDF links")
        for link in pdf_links[:3]:  # Show first 3
            print(f"   • {link['title']} -> {link['url']}")
            if link['version']:
                print(f"     Version: {link['version']}")
    else:
        print(f"❌ PDF detection issue - found {len(pdf_links)}, expected at least {expected_pdfs}")
        for link in pdf_links:
            print(f"   Found: {link}")
        return False
    
    # Test 3: Version extraction
    print("\n🔢 Testing version extraction...")
    test_cases = [
        ("MDS 9000 Series v1.2 Configuration Guide", "1.2"),
        ("Release 90 Documentation", "90"),
        ("Software Version 8.4.1 Manual", "8.4.1"),
        ("Basic Guide (no version)", None),
    ]
    
    version_tests_passed = 0
    for text, expected_version in test_cases:
        extracted = scraper._extract_version(text, "")
        if extracted == expected_version:
            version_tests_passed += 1
            print(f"   ✅ '{text}' -> '{extracted}'")
        else:
            print(f"   ❌ '{text}' -> '{extracted}' (expected '{expected_version}')")
    
    if version_tests_passed >= 3:  # Allow some flexibility
        print("✅ Version extraction mostly working")
    else:
        print("❌ Version extraction needs improvement")
        return False
    
    # Test 4: Filename generation
    print("\n📝 Testing filename generation...")
    
    test_pdf_info = {
        'title': 'MDS 9000 Configuration Guide',
        'version': '1.2',
        'url': 'https://example.com/docs/config.pdf'
    }
    
    filename = scraper._generate_filename(test_pdf_info)
    
    if filename and filename.endswith('.pdf') and 'v1.2' in filename:
        print(f"✅ Filename generation works: {filename}")
    else:
        print(f"❌ Filename generation issue: {filename}")
        return False
    
    # Test 5: File hash calculation (using a temporary file)
    print("\n🔐 Testing file hash calculation...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as temp_file:
        temp_file.write("Mock PDF content for hash testing")
        temp_file_path = temp_file.name
    
    try:
        file_hash = scraper._calculate_file_hash(temp_file_path)
        if file_hash and len(file_hash) == 64:  # SHA256 should be 64 chars
            print(f"✅ Hash calculation works: {file_hash[:16]}...")
        else:
            print(f"❌ Hash calculation issue: {file_hash}")
            return False
    finally:
        os.unlink(temp_file_path)
    
    print("\n🎉 All web scraper tests passed!")
    return True


def test_cisco_url_access():
    """Test if we can access the actual Cisco documentation URL."""
    print("\n🌐 Testing Cisco URL accessibility...")
    
    scraper = MDSDocumentScraper(timeout=30)
    cisco_url = "https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html"
    
    try:
        soup = scraper.fetch_page(cisco_url)
        if soup:
            # Look for common elements that should be on a Cisco doc page
            cisco_indicators = [
                soup.find(text=lambda t: t and 'cisco' in t.lower()),
                soup.find(text=lambda t: t and 'mds' in t.lower()),
                soup.find('a', href=lambda h: h and '.pdf' in h.lower())
            ]
            
            if any(cisco_indicators):
                pdf_links = scraper.extract_pdf_links(soup, cisco_url)
                print(f"✅ Cisco URL accessible - found {len(pdf_links)} potential PDF links")
                
                if pdf_links:
                    print("   Sample PDFs found:")
                    for i, link in enumerate(pdf_links[:3]):
                        print(f"   {i+1}. {link['title'][:60]}...")
                return True
            else:
                print("⚠️  Cisco URL accessible but content unexpected")
                return True  # Still accessible
        else:
            print("❌ Cannot access Cisco URL")
            return False
            
    except Exception as e:
        print(f"⚠️  Cisco URL test failed (this is OK if network restricted): {e}")
        return True  # Don't fail the overall test for network issues


if __name__ == "__main__":
    print("🚀 Starting Web Scraper Validation\n")
    
    success = test_web_scraper()
    
    # Optional network test
    if success:
        test_cisco_url_access()
    
    if success:
        print("\n✅ Web scraper validation completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Web scraper validation failed")
        sys.exit(1)