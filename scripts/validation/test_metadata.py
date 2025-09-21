"""
Validation script for metadata manager functionality.
Run this to test the metadata management system.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from metadata import MetadataManager


def test_metadata_manager():
    """Test the metadata manager functionality."""
    print("🧪 Testing Metadata Manager...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
        db_path = db_file.name
    
    try:
        # Initialize manager
        manager = MetadataManager(db_path)
        print("✅ Database initialized successfully")
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as test_file:
            test_file.write("Test document content for validation")
            test_file_path = test_file.name
        
        try:
            # Test hash calculation
            file_hash = manager.calculate_file_hash(test_file_path)
            print(f"✅ Hash calculated: {file_hash[:16]}...")
            
            # Test file size
            file_size = os.path.getsize(test_file_path)
            print(f"✅ File size: {file_size} bytes")
            
            # Test document addition
            doc_id = manager.add_document(
                url="https://test.com/validation.pdf",
                filename="validation_test.pdf",
                file_path=test_file_path,
                file_size=file_size,
                file_hash=file_hash,
                version="1.0"
            )
            print(f"✅ Document added with ID: {doc_id}")
            
            # Test document exists check
            exists = manager.document_exists("https://test.com/validation.pdf", file_hash)
            assert exists, "Document should exist"
            print("✅ Document existence check passed")
            
            # Test get current document
            current_doc = manager.get_current_document("https://test.com/validation.pdf")
            assert current_doc is not None, "Should find current document"
            print("✅ Get current document passed")
            
            # Test get all documents
            all_docs = manager.get_all_documents()
            assert len(all_docs) == 1, "Should have one document"
            print("✅ Get all documents passed")
            
            # Test download history logging
            manager.log_download_attempt("https://test.com/validation.pdf", "success")
            history = manager.get_download_history()
            assert len(history) >= 1, "Should have download history"
            print("✅ Download history logging passed")
            
            # Test archiving
            manager.archive_document(doc_id, "/archive/path/validation_test.pdf")
            archived_doc = manager.get_current_document("https://test.com/validation.pdf")
            assert archived_doc is None, "Document should no longer be current"
            print("✅ Document archiving passed")
            
            print("\n🎉 All metadata manager tests passed!")
            return True
            
        finally:
            # Cleanup test file
            os.unlink(test_file_path)
    
    finally:
        # Cleanup database
        os.unlink(db_path)
    
    return False


if __name__ == "__main__":
    success = test_metadata_manager()
    if not success:
        print("❌ Metadata manager validation failed")
        sys.exit(1)
    else:
        print("✅ Metadata manager validation completed successfully")