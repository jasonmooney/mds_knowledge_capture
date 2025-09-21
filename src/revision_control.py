"""
Revision control system for MDS documentation.
Handles archiving of old versions and maintaining current documents.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import json

from metadata import MetadataManager

logger = logging.getLogger(__name__)


class RevisionController:
    """Manages document versions and archiving."""
    
    def __init__(
        self,
        current_path: str = "knowledge_source/current",
        archive_path: str = "knowledge_source/archive", 
        metadata_manager: Optional[MetadataManager] = None
    ):
        """Initialize revision controller."""
        self.current_path = Path(current_path)
        self.archive_path = Path(archive_path)
        self.metadata_manager = metadata_manager or MetadataManager()
        
        # Ensure directories exist
        self.current_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"RevisionController initialized with current: {self.current_path}, archive: {self.archive_path}")
    
    def check_for_updates(self, new_documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Check which documents are new or updated.
        Returns list of documents that need processing.
        """
        documents_to_process = []
        
        for doc in new_documents:
            url = doc['url']
            new_hash = doc['sha256_hash']
            
            # Check if document already exists with same hash
            if self.metadata_manager.document_exists(url, new_hash):
                logger.info(f"Document {doc['filename']} already exists with same content, skipping")
                continue
            
            # Check if there's a current version
            current_doc = self.metadata_manager.get_current_document(url)
            
            if current_doc:
                if current_doc['sha256_hash'] != new_hash:
                    logger.info(f"Document {doc['filename']} has been updated (hash mismatch)")
                    doc['is_update'] = True
                    doc['previous_version'] = current_doc
                    documents_to_process.append(doc)
                else:
                    logger.info(f"Document {doc['filename']} is identical to current version")
            else:
                logger.info(f"Document {doc['filename']} is new")
                doc['is_update'] = False
                documents_to_process.append(doc)
        
        logger.info(f"Found {len(documents_to_process)} documents to process")
        return documents_to_process
    
    def archive_old_version(self, old_doc: Dict[str, str]) -> str:
        """
        Archive an old version of a document.
        Returns the new archive path.
        """
        try:
            old_file_path = Path(old_doc['file_path'])
            
            if not old_file_path.exists():
                logger.warning(f"Old file {old_file_path} does not exist, cannot archive")
                return None
            
            # Create archive directory structure by date
            archive_date = datetime.now().strftime("%Y/%m/%d")
            archive_dir = self.archive_path / archive_date
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime("%H%M%S")
            original_name = old_file_path.stem  # filename without extension
            archive_filename = f"{original_name}_archived_{timestamp}.pdf"
            archive_file_path = archive_dir / archive_filename
            
            # Move file to archive
            shutil.move(str(old_file_path), str(archive_file_path))
            
            # Update database record
            self.metadata_manager.archive_document(old_doc['id'], str(archive_file_path))
            
            logger.info(f"Archived {old_file_path.name} -> {archive_file_path}")
            return str(archive_file_path)
            
        except Exception as e:
            logger.error(f"Error archiving {old_doc.get('filename', 'unknown')}: {e}")
            return None
    
    def place_current_version(self, doc: Dict[str, str]) -> str:
        """
        Place a new document in the current directory.
        Returns the final file path.
        """
        try:
            source_path = Path(doc['file_path'])
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source file {source_path} does not exist")
            
            # Generate clean filename for current version
            clean_filename = self._generate_current_filename(doc)
            target_path = self.current_path / clean_filename
            
            # Handle name conflicts
            counter = 1
            base_name = target_path.stem
            while target_path.exists():
                target_path = self.current_path / f"{base_name}_{counter}.pdf"
                counter += 1
            
            # Copy or move file to current directory
            if source_path.parent != self.current_path:
                if source_path.parent.name == 'current':
                    # Already in current, just rename if needed
                    if source_path != target_path:
                        shutil.move(str(source_path), str(target_path))
                else:
                    # Copy from download location to current
                    shutil.copy2(str(source_path), str(target_path))
            
            logger.info(f"Placed current version: {target_path.name}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"Error placing current version of {doc.get('filename', 'unknown')}: {e}")
            raise
    
    def _generate_current_filename(self, doc: Dict[str, str]) -> str:
        """Generate a clean filename for the current version."""
        # Use original filename as base
        original_name = Path(doc['filename']).stem
        
        # Clean up the name - remove date stamps and version info if present
        clean_name = original_name
        
        # Remove common date patterns
        import re
        clean_name = re.sub(r'_\d{8}(_\d{6})?', '', clean_name)  # Remove _YYYYMMDD(_HHMMSS)
        clean_name = re.sub(r'_v?\d+\.\d+(\.\d+)?', '', clean_name)  # Remove version numbers
        
        # Add version if available and not already present
        if doc.get('version') and f"v{doc['version']}" not in clean_name:
            clean_name += f"_v{doc['version']}"
        
        # Ensure reasonable length
        if len(clean_name) > 100:
            clean_name = clean_name[:100]
        
        return f"{clean_name}.pdf"
    
    def process_documents(self, new_documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Main method to process new documents with revision control.
        Returns list of successfully processed documents.
        """
        logger.info(f"Processing {len(new_documents)} documents with revision control")
        
        # Check which documents need processing
        documents_to_process = self.check_for_updates(new_documents)
        
        processed_documents = []
        
        for doc in documents_to_process:
            try:
                # Archive old version if this is an update
                if doc.get('is_update') and doc.get('previous_version'):
                    old_doc = doc['previous_version']
                    archive_path = self.archive_old_version(old_doc)
                    if archive_path:
                        doc['archived_previous'] = archive_path
                
                # Place new version as current
                current_path = self.place_current_version(doc)
                doc['current_file_path'] = current_path
                
                # Update metadata
                doc_id = self.metadata_manager.add_document(
                    url=doc['url'],
                    filename=Path(current_path).name,
                    file_path=current_path,
                    file_size=doc['file_size'],
                    file_hash=doc['sha256_hash'],
                    version=doc.get('version')
                )
                
                doc['doc_id'] = doc_id
                processed_documents.append(doc)
                
                logger.info(f"Successfully processed document: {Path(current_path).name}")
                
            except Exception as e:
                logger.error(f"Failed to process document {doc.get('filename', 'unknown')}: {e}")
                # Log the attempt as failed
                self.metadata_manager.log_download_attempt(
                    doc['url'], 
                    'processing_failed', 
                    str(e)
                )
        
        logger.info(f"Successfully processed {len(processed_documents)}/{len(documents_to_process)} documents")
        return processed_documents
    
    def cleanup_old_archives(self, days_old: int = 180) -> int:
        """
        Clean up old archived files and database entries.
        Returns number of files cleaned up.
        """
        logger.info(f"Cleaning up archives older than {days_old} days")
        
        cutoff_date = datetime.now().replace(days=-days_old)
        cleaned_files = 0
        
        # Walk through archive directory
        for root, dirs, files in os.walk(self.archive_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = Path(root) / file
                    try:
                        # Check file modification time
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_time < cutoff_date:
                            file_path.unlink()
                            cleaned_files += 1
                            logger.debug(f"Deleted old archive: {file_path}")
                            
                    except Exception as e:
                        logger.error(f"Error processing archive file {file_path}: {e}")
        
        # Clean up database entries
        db_cleaned = self.metadata_manager.cleanup_old_entries(days_old)
        
        logger.info(f"Cleanup complete: {cleaned_files} files, {db_cleaned} database entries removed")
        return cleaned_files
    
    def get_revision_history(self, url: str) -> List[Dict[str, str]]:
        """Get revision history for a specific URL."""
        all_docs = self.metadata_manager.get_all_documents()
        url_docs = [doc for doc in all_docs if doc['url'] == url]
        
        # Sort by download date
        url_docs.sort(key=lambda x: x['download_date'], reverse=True)
        
        return url_docs
    
    def get_current_inventory(self) -> List[Dict[str, str]]:
        """Get list of all current documents."""
        return self.metadata_manager.get_all_documents(current_only=True)


if __name__ == "__main__":
    # Simple validation test
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🧪 Testing RevisionController...")
        
        # Setup paths
        current_dir = Path(temp_dir) / "current"
        archive_dir = Path(temp_dir) / "archive"
        db_path = Path(temp_dir) / "test.db"
        
        # Create test metadata manager
        metadata_mgr = MetadataManager(str(db_path))
        
        # Initialize revision controller
        revision_ctrl = RevisionController(
            current_path=str(current_dir),
            archive_path=str(archive_dir),
            metadata_manager=metadata_mgr
        )
        
        # Create a test document
        test_file = current_dir / "test_doc.pdf"
        test_file.write_text("Test document content")
        
        test_doc = {
            'url': 'https://test.com/doc.pdf',
            'filename': 'test_doc.pdf',
            'file_path': str(test_file),
            'file_size': test_file.stat().st_size,
            'sha256_hash': 'abcd1234',
            'version': '1.0'
        }
        
        # Process document
        processed = revision_ctrl.process_documents([test_doc])
        
        if processed:
            print("✅ RevisionController basic functionality works")
            print(f"   Processed: {processed[0]['current_file_path']}")
            
            # Test inventory
            inventory = revision_ctrl.get_current_inventory()
            print(f"✅ Current inventory: {len(inventory)} documents")
        else:
            print("❌ RevisionController failed")
            
        print("✅ RevisionController validation complete")