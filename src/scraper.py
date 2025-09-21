"""
Web scraper for Cisco MDS documentation.
Handles PDF detection, download, and URL management.
"""

import asyncio
import aiohttp
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import re
import logging
from pathlib import Path
import hashlib
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class MDSDocumentScraper:
    """Scrapes and downloads MDS documentation PDFs."""
    
    def __init__(
        self,
        user_agent: str = "MDS-Knowledge-Capture-Agent/1.0",
        timeout: int = 300,
        max_concurrent: int = 5
    ):
        """Initialize scraper with configuration."""
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session_headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            logger.info(f"Fetching page: {url}")
            response = requests.get(
                url, 
                headers=self.session_headers, 
                timeout=self.timeout,
                verify=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"Successfully parsed page: {url}")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {url}: {e}")
            return None
    
    def extract_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract PDF links from parsed HTML."""
        pdf_links = []
        
        # Find all links that might be PDFs
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Skip empty or invalid hrefs
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Check if it's a PDF
            if self._is_pdf_link(full_url, link.get_text(strip=True)):
                # Extract version information if possible
                version = self._extract_version(link.get_text(strip=True), href)
                
                pdf_info = {
                    'url': full_url,
                    'title': link.get_text(strip=True),
                    'version': version,
                    'discovered_from': base_url
                }
                pdf_links.append(pdf_info)
                logger.debug(f"Found PDF: {pdf_info}")
        
        logger.info(f"Found {len(pdf_links)} PDF links on {base_url}")
        return pdf_links
    
    def _is_pdf_link(self, url: str, link_text: str) -> bool:
        """Determine if a URL/link is likely a PDF."""
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        # Direct PDF extension check
        if url_lower.endswith('.pdf'):
            return True
        
        # Check for PDF in query parameters or fragments
        if 'filetype=pdf' in url_lower or 'type=pdf' in url_lower:
            return True
        
        # Check link text for PDF indicators
        pdf_indicators = ['pdf', 'guide', 'manual', 'document', 'datasheet', 'configuration']
        if any(indicator in text_lower for indicator in pdf_indicators):
            # Additional check to avoid false positives
            if 'html' not in url_lower and 'htm' not in url_lower:
                return True
        
        return False
    
    def _extract_version(self, link_text: str, href: str) -> Optional[str]:
        """Extract version information from link text or URL."""
        # Common version patterns
        version_patterns = [
            r'v?(\d+\.\d+(?:\.\d+)?)',  # v1.2.3 or 1.2.3
            r'rel(\d+)',                # rel90
            r'release[_\s](\d+)',       # release_90
            r'version[_\s](\d+\.\d+)',  # version_9.0
        ]
        
        # Search in link text first
        for pattern in version_patterns:
            match = re.search(pattern, link_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Search in URL
        for pattern in version_patterns:
            match = re.search(pattern, href, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def download_pdf(self, pdf_info: Dict[str, str], download_path: str) -> Optional[Dict[str, str]]:
        """Download a PDF file asynchronously."""
        try:
            url = pdf_info['url']
            filename = self._generate_filename(pdf_info)
            file_path = os.path.join(download_path, filename)
            
            logger.info(f"Downloading {url} -> {filename}")
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.session_headers
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'application/pdf' not in content_type and not url.endswith('.pdf'):
                        logger.warning(f"Unexpected content type for {url}: {content_type}")
                    
                    # Create directory if it doesn't exist
                    os.makedirs(download_path, exist_ok=True)
                    
                    # Download file
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            # Verify file was downloaded
            if not os.path.exists(file_path):
                raise Exception("File was not created")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("Downloaded file is empty")
            
            # Calculate hash
            file_hash = self._calculate_file_hash(file_path)
            
            result = {
                'url': url,
                'filename': filename,
                'file_path': file_path,
                'file_size': file_size,
                'sha256_hash': file_hash,
                'download_time': datetime.now().isoformat(),
                'version': pdf_info.get('version'),
                'title': pdf_info.get('title', '')
            }
            
            logger.info(f"Successfully downloaded {filename} ({file_size} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"Error downloading {pdf_info['url']}: {e}")
            return None
    
    def _generate_filename(self, pdf_info: Dict[str, str]) -> str:
        """Generate a standardized filename for downloaded PDF."""
        # Extract meaningful parts
        title = pdf_info.get('title', '')
        version = pdf_info.get('version', '')
        url = pdf_info['url']
        
        # Clean title for filename
        clean_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', title)
        clean_title = re.sub(r'\s+', '_', clean_title.strip())
        
        # Use URL filename as fallback
        url_filename = os.path.basename(urlparse(url).path)
        if url_filename and url_filename.endswith('.pdf'):
            base_name = url_filename[:-4]  # Remove .pdf extension
        else:
            base_name = clean_title or 'mds_document'
        
        # Add version if available
        if version:
            base_name += f"_v{version}"
        
        # Add date for uniqueness
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{base_name}_{date_str}.pdf"
        
        # Ensure filename isn't too long
        if len(filename) > 200:
            filename = filename[:190] + f"_{date_str}.pdf"
        
        return filename
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of downloaded file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def scrape_and_download(
        self, 
        primary_url: str, 
        download_path: str,
        one_time_urls: List[str] = None
    ) -> List[Dict[str, str]]:
        """Main method to scrape URLs and download PDFs."""
        all_results = []
        
        # Scrape primary URL
        logger.info(f"Starting scrape of primary URL: {primary_url}")
        soup = self.fetch_page(primary_url)
        
        if soup:
            pdf_links = self.extract_pdf_links(soup, primary_url)
            
            # Download PDFs with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def download_with_limit(pdf_info):
                async with semaphore:
                    return await self.download_pdf(pdf_info, download_path)
            
            download_tasks = [download_with_limit(pdf_info) for pdf_info in pdf_links]
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Filter successful downloads
            for result in results:
                if isinstance(result, dict) and result:
                    all_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Download failed with exception: {result}")
        
        # Process one-time URLs if provided
        if one_time_urls:
            logger.info(f"Processing {len(one_time_urls)} one-time URLs")
            for url in one_time_urls:
                if url.lower().endswith('.pdf'):
                    # Direct PDF download
                    pdf_info = {
                        'url': url,
                        'title': os.path.basename(urlparse(url).path),
                        'version': None,
                        'discovered_from': 'one_time_url'
                    }
                    result = await self.download_pdf(pdf_info, download_path)
                    if result:
                        all_results.append(result)
                else:
                    # Scrape page for PDFs
                    soup = self.fetch_page(url)
                    if soup:
                        pdf_links = self.extract_pdf_links(soup, url)
                        for pdf_info in pdf_links:
                            result = await self.download_pdf(pdf_info, download_path)
                            if result:
                                all_results.append(result)
        
        logger.info(f"Total successful downloads: {len(all_results)}")
        return all_results
    
    def extract_document_info(self, url: str) -> Dict[str, str]:
        """Extract document information from URL patterns."""
        # Default document info
        doc_info = {
            'title': 'Unknown Document',
            'category': 'General',
            'version': 'Unknown',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Extract from URL patterns
        filename = url.split('/')[-1].replace('.html', '').replace('.pdf', '')
        
        # Categorization logic
        if 'release-notes' in url:
            if 'transceivers' in url:
                doc_info['category'] = 'Transceiver Release Notes'
                doc_info['title'] = 'MDS 9000 Series Transceivers Release Notes'
            else:
                doc_info['category'] = 'System Release Notes'
                doc_info['title'] = 'MDS 9000 NX-OS Release Notes'
        elif 'command' in url:
            doc_info['category'] = 'Command Reference'
            doc_info['title'] = 'MDS 9000 NX-OS Command Reference Guide'
        elif 'Recommended_Releases' in url:
            doc_info['category'] = 'Recommended Releases'
            doc_info['title'] = 'MDS NX-OS Recommended Releases'
        elif 'roadmaps' in url:
            doc_info['category'] = 'Roadmap'
            doc_info['title'] = 'MDS 9000 Release Roadmap'
        
        # Version extraction
        if '944' in url:
            doc_info['version'] = '9.4.4'
        elif '9x' in url:
            doc_info['version'] = '9.x'
        elif 'rel90' in url:
            doc_info['version'] = '9.0'
            
        return doc_info


# Synchronous wrapper function for easier testing
def run_scraper(primary_url: str, download_path: str, one_time_urls: List[str] = None) -> List[Dict[str, str]]:
    """Synchronous wrapper for the scraper."""
    scraper = MDSDocumentScraper()
    return asyncio.run(scraper.scrape_and_download(primary_url, download_path, one_time_urls))


if __name__ == "__main__":
    # Simple test - this will be moved to validation scripts
    import tempfile
    import shutil
    
    logging.basicConfig(level=logging.INFO)
    
    # Test URL (using a known PDF-containing documentation page)
    test_url = "https://www.cisco.com/c/en/us/td/docs/storage/san_switches/mds9000/roadmaps/rel90.html"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing scraper with temporary directory: {temp_dir}")
        
        scraper = MDSDocumentScraper(max_concurrent=2, timeout=60)
        
        # Test page fetching
        soup = scraper.fetch_page(test_url)
        if soup:
            print("✅ Page fetching works")
            
            # Test PDF extraction
            pdf_links = scraper.extract_pdf_links(soup, test_url)
            print(f"✅ Found {len(pdf_links)} potential PDF links")
            
            if pdf_links:
                print("Sample PDF links:")
                for i, link in enumerate(pdf_links[:3]):  # Show first 3
                    print(f"  {i+1}. {link['title'][:50]}... -> {link['url']}")
        else:
            print("❌ Could not fetch test page")
        
        print("✅ Web scraper validation complete")