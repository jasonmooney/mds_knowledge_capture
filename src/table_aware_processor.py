"""
Table-Aware Document Processor for preserving structured content in RAG systems.
This processor identifies and preserves table structures during document chunking.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a detected table structure."""
    start_pos: int
    end_pos: int
    content: str
    title: Optional[str] = None
    table_type: str = "generic"
    context_before: str = ""
    context_after: str = ""


class TableAwareProcessor:
    """Enhanced processor that preserves table structures during document chunking."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        table_chunk_size: int = 2000,  # Larger chunks for tables
        preserve_context: int = 200     # Context to preserve around tables
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.table_chunk_size = table_chunk_size
        self.preserve_context = preserve_context
        
        # Initialize text splitters
        self.standard_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.table_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.table_chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n"]  # More conservative for tables
        )
        
        logger.info(f"✅ Table-aware processor initialized")
        logger.info(f"   📄 Standard chunks: {self.chunk_size} chars")
        logger.info(f"   📊 Table chunks: {self.table_chunk_size} chars")
    
    def detect_tables(self, text: str) -> List[TableInfo]:
        """Detect table structures in text using various patterns."""
        tables = []
        
        # Pattern 1: Structured tables with headers and consistent formatting
        # Look for "Product Impact | Feature | Description" style tables
        table_pattern = r"""
            (?P<title>[^\n]*(?:features?|table|matrix)[^\n]*\n)?  # Optional title
            (?P<header>[^\n]+\|[^\n]+\|[^\n]+[^\n]*\n)?          # Header row with pipes
            (?P<content>(?:[^\n]*\|[^\n]*\|[^\n]*\n?)+)          # Content rows with pipes
        """
        
        for match in re.finditer(table_pattern, text, re.VERBOSE | re.IGNORECASE | re.MULTILINE):
            start_pos = match.start()
            end_pos = match.end()
            table_content = match.group(0)
            title = match.group('title') or ""
            
            tables.append(TableInfo(
                start_pos=start_pos,
                end_pos=end_pos,
                content=table_content.strip(),
                title=title.strip(),
                table_type="structured_table",
                context_before=self._get_context_before(text, start_pos),
                context_after=self._get_context_after(text, end_pos)
            ))
        
        # Pattern 2: Feature tables with "Product Impact", "Feature", "Description" structure
        feature_table_pattern = r"""
            (?P<intro>New\s+software\s+features[^\n]*\n)           # Table introduction
            \s*                                                    # Optional whitespace
            (?P<header>Product\s+Impact[^\n]*Feature[^\n]*Description[^\n]*\n)? # Optional header
            \s*                                                    # Optional whitespace
            (?P<content>                                           # Content section
                (?:(?:Ease\s+of\s+Use|Feature\s+Set|Interoperability|Security)[^\n]*\n  # Category headers
                (?:(?!(?:Ease\s+of\s+Use|Feature\s+Set|Interoperability|Security|New\s+hardware\s+features|Resolved\s+issues))[^\n]*\n?)*  # Content under category
                )+
            )
        """
        
        for match in re.finditer(feature_table_pattern, text, re.VERBOSE | re.IGNORECASE | re.MULTILINE):
            start_pos = match.start()
            end_pos = match.end()
            table_content = match.group(0)
            
            tables.append(TableInfo(
                start_pos=start_pos,
                end_pos=end_pos,
                content=table_content.strip(),
                title="New Software Features",
                table_type="feature_table",
                context_before=self._get_context_before(text, start_pos),
                context_after=self._get_context_after(text, end_pos)
            ))
        
        # Pattern 3: Simplified feature detection - look for feature sections
        simple_feature_pattern = r"""
            New\s+software\s+features[^\n]*\n                     # Section header
            (?P<content>                                           # Everything until next major section
                (?:(?!New\s+hardware\s+features|Resolved\s+issues|Open\s+Issues)[^\n]*\n?)+
            )
        """
        
        for match in re.finditer(simple_feature_pattern, text, re.VERBOSE | re.IGNORECASE | re.MULTILINE):
            start_pos = match.start()
            end_pos = match.end()
            table_content = match.group(0)
            
            # Only add if we haven't already captured this content
            if not any(t.start_pos <= start_pos < t.end_pos for t in tables):
                tables.append(TableInfo(
                    start_pos=start_pos,
                    end_pos=end_pos,
                    content=table_content.strip(),
                    title="New Software Features (Complete)",
                    table_type="complete_feature_section",
                    context_before=self._get_context_before(text, start_pos),
                    context_after=self._get_context_after(text, end_pos)
                ))
        
        # Sort tables by position
        tables.sort(key=lambda t: t.start_pos)
        
        # Remove overlapping tables (keep the most specific one)
        filtered_tables = []
        for table in tables:
            # Check if this table overlaps significantly with existing ones
            overlaps = False
            for existing in filtered_tables:
                if (table.start_pos < existing.end_pos and table.end_pos > existing.start_pos):
                    # If more than 50% overlap, skip this table
                    overlap_size = min(table.end_pos, existing.end_pos) - max(table.start_pos, existing.start_pos)
                    table_size = table.end_pos - table.start_pos
                    if overlap_size / table_size > 0.5:
                        overlaps = True
                        break
            
            if not overlaps:
                filtered_tables.append(table)
        
        logger.info(f"📊 Detected {len(filtered_tables)} table structures")
        for i, table in enumerate(filtered_tables):
            logger.info(f"   Table {i+1}: {table.table_type} - '{table.title}' ({len(table.content)} chars)")
        
        return filtered_tables
    
    def _get_context_before(self, text: str, pos: int) -> str:
        """Get context before the table."""
        start = max(0, pos - self.preserve_context)
        return text[start:pos].strip()
    
    def _get_context_after(self, text: str, pos: int) -> str:
        """Get context after the table."""
        end = min(len(text), pos + self.preserve_context)
        return text[pos:end].strip()
    
    def create_table_chunk(self, table: TableInfo, source_metadata: Dict) -> Document:
        """Create a specialized chunk for table content."""
        # Combine title, content, and context for comprehensive understanding
        full_content = []
        
        if table.context_before:
            full_content.append(f"Context before: {table.context_before}")
        
        if table.title and table.title not in table.content:
            full_content.append(f"Table: {table.title}")
        
        full_content.append(table.content)
        
        if table.context_after:
            full_content.append(f"Context after: {table.context_after}")
        
        combined_content = "\n\n".join(full_content)
        
        # Enhanced metadata for table chunks
        enhanced_metadata = source_metadata.copy()
        enhanced_metadata.update({
            'chunk_type': 'table',
            'table_type': table.table_type,
            'table_title': table.title or 'Unknown Table',
            'is_structured_content': True,
            'content_category': 'features' if 'feature' in table.table_type.lower() else 'documentation'
        })
        
        return Document(
            page_content=combined_content,
            metadata=enhanced_metadata
        )
    
    def smart_chunk_document(self, document: Document) -> List[Document]:
        """Smart chunking that preserves table structures."""
        text = document.page_content
        source_metadata = document.metadata
        
        # Detect tables
        tables = self.detect_tables(text)
        
        if not tables:
            # No tables found, use standard chunking
            logger.debug("No tables detected, using standard chunking")
            chunks = self.standard_splitter.split_documents([document])
            # Mark as standard chunks
            for chunk in chunks:
                chunk.metadata['chunk_type'] = 'standard'
                chunk.metadata['is_structured_content'] = False
            return chunks
        
        # Process document with table-aware chunking
        result_chunks = []
        last_end = 0
        
        for table in tables:
            # Add standard chunks before the table
            if table.start_pos > last_end:
                before_table_text = text[last_end:table.start_pos].strip()
                if before_table_text:
                    before_doc = Document(
                        page_content=before_table_text,
                        metadata=source_metadata.copy()
                    )
                    before_chunks = self.standard_splitter.split_documents([before_doc])
                    for chunk in before_chunks:
                        chunk.metadata['chunk_type'] = 'standard'
                        chunk.metadata['is_structured_content'] = False
                    result_chunks.extend(before_chunks)
            
            # Add the table as a specialized chunk
            table_chunk = self.create_table_chunk(table, source_metadata)
            result_chunks.append(table_chunk)
            
            last_end = table.end_pos
        
        # Add remaining text after the last table
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                remaining_doc = Document(
                    page_content=remaining_text,
                    metadata=source_metadata.copy()
                )
                remaining_chunks = self.standard_splitter.split_documents([remaining_doc])
                for chunk in remaining_chunks:
                    chunk.metadata['chunk_type'] = 'standard'
                    chunk.metadata['is_structured_content'] = False
                result_chunks.extend(remaining_chunks)
        
        logger.info(f"📄 Created {len(result_chunks)} chunks (including {len(tables)} table chunks)")
        return result_chunks


def main():
    """Test the table-aware processor."""
    logging.basicConfig(level=logging.INFO)
    
    processor = TableAwareProcessor()
    
    # Test with sample text that mimics the release notes structure
    sample_text = """
Cisco MDS 9000 Series Switches, Release 9.4(4)

New software features

Product Impact Feature Description 
Ease of Use Fabric Congestion and 
Diagnostics 
Support to send on-demand RDF commands to proactively 
inform HBAs of new fabric capabilities after a non-disruptive 
upgrade. 

For more information, see the Cisco MDS 9000 Series 
Interfaces Configuration Guide. 

System Information The show fabric switch information command has been 
enhanced to display switch serial numbers. 

For more information, see the Cisco MDS 9000 Series 
Command Reference. 

Feature Set Smart Monitoring and Alerting 
(SMA) 
The SMA feature has been changed to production-ready. SMA 
provides unified monitoring and timely detection of important 
events or conditions. It generates proactive notifications and 
helps in maintaining the health of the system.

Security AES-256 encryption for SNMP Support for AES-256 encryption key for SNMP has been 
added. 

For more information, see the Cisco MDS 9000 Series Security 
Configuration Guide.

New hardware features

There are no new hardware features in this release.
"""
    
    # Create a test document
    test_doc = Document(
        page_content=sample_text,
        metadata={'source': 'test_release_notes.pdf'}
    )
    
    # Process with table-aware chunking
    chunks = processor.smart_chunk_document(test_doc)
    
    print(f"\n📊 Table-Aware Processing Results:")
    print("=" * 60)
    print(f"Total chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        chunk_type = chunk.metadata.get('chunk_type', 'unknown')
        is_structured = chunk.metadata.get('is_structured_content', False)
        table_title = chunk.metadata.get('table_title', '')
        
        print(f"\nChunk {i+1}: {chunk_type}")
        if is_structured:
            print(f"  Table: {table_title}")
        print(f"  Length: {len(chunk.page_content)} characters")
        print(f"  Preview: {chunk.page_content[:100]}...")


if __name__ == "__main__":
    main()