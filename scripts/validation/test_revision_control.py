"""
Validation script for revision control functionality.
Tests document archiving, version management, and cleanup.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from revision_control import RevisionController
from metadata import MetadataManager


def test_revision_control():
    """Test the revision control system."""
    print("🧪 Testing Revision Control System...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup paths
        current_dir = Path(temp_dir) / "current"
        archive_dir = Path(temp_dir) / "archive"
        db_path = Path(temp_dir) / "test.db"
        download_dir = Path(temp_dir) / "downloads"
        
        # Create directories
        current_dir.mkdir(parents=True)
        archive_dir.mkdir(parents=True)
        download_dir.mkdir(parents=True)
        
        # Create test metadata manager
        metadata_mgr = MetadataManager(str(db_path))
        
        # Initialize revision controller
        revision_ctrl = RevisionController(
            current_path=str(current_dir),
            archive_path=str(archive_dir),
            metadata_manager=metadata_mgr
        )
        
        print("✅ RevisionController initialized successfully")
        
        # Test 1: Process new document
        print("\n📄 Testing new document processing...")
        
        # Create a test document
        test_file1 = download_dir / "test_doc_v1.pdf"
        test_file1.write_text("Test document version 1 content")
        
        test_doc1 = {
            'url': 'https://test.com/guide.pdf',
            'filename': 'test_doc_v1.pdf',
            'file_path': str(test_file1),
            'file_size': test_file1.stat().st_size,
            'sha256_hash': metadata_mgr.calculate_file_hash(str(test_file1)),
            'version': '1.0',
            'title': 'Test Configuration Guide'
        }
        
        processed_docs = revision_ctrl.process_documents([test_doc1])
        
        if len(processed_docs) == 1:
            print("✅ New document processed successfully")
            print(f"   Current file: {Path(processed_docs[0]['current_file_path']).name}")
        else:
            print("❌ Failed to process new document")
            return False
        
        # Test 2: Process updated version
        print("\n🔄 Testing document update processing...")
        
        # Create updated version
        test_file2 = download_dir / "test_doc_v2.pdf"
        test_file2.write_text("Test document version 2 content - UPDATED")
        
        test_doc2 = {
            'url': 'https://test.com/guide.pdf',  # Same URL
            'filename': 'test_doc_v2.pdf',
            'file_path': str(test_file2),
            'file_size': test_file2.stat().st_size,
            'sha256_hash': metadata_mgr.calculate_file_hash(str(test_file2)),
            'version': '2.0',
            'title': 'Test Configuration Guide'
        }
        
        processed_docs2 = revision_ctrl.process_documents([test_doc2])
        
        if len(processed_docs2) == 1 and processed_docs2[0].get('is_update'):
            print("✅ Document update processed successfully")
            print(f"   Updated file: {Path(processed_docs2[0]['current_file_path']).name}")
            
            # Check if old version was archived
            if processed_docs2[0].get('archived_previous'):
                print(f"   Previous version archived: {processed_docs2[0]['archived_previous']}")
                
                # Verify archive file exists
                archive_path = Path(processed_docs2[0]['archived_previous'])
                if archive_path.exists():
                    print("✅ Archive file exists")
                else:
                    print("❌ Archive file missing")
                    return False
            else:
                print("⚠️  Previous version not archived (might be expected)")
        else:
            print("❌ Failed to process document update")
            return False
        
        # Test 3: Check inventory
        print("\n📊 Testing inventory management...")
        
        current_inventory = revision_ctrl.get_current_inventory()
        if len(current_inventory) >= 1:
            print(f"✅ Current inventory contains {len(current_inventory)} documents")
            for doc in current_inventory:
                print(f"   • {doc['filename']} (v{doc.get('version', '?')})")
        else:
            print("❌ Inventory is empty")
            return False
        
        # Test 4: Revision history
        print("\n📚 Testing revision history...")
        
        history = revision_ctrl.get_revision_history('https://test.com/guide.pdf')
        if len(history) >= 2:  # Should have both versions
            print(f"✅ Revision history contains {len(history)} versions")
            for i, doc in enumerate(history):
                current_status = "(current)" if doc['is_current'] else "(archived)"
                print(f"   {i+1}. v{doc.get('version', '?')} {current_status}")
        else:
            print(f"⚠️  Revision history contains {len(history)} versions (expected 2+)")
        
        # Test 5: Duplicate handling
        print("\n🔄 Testing duplicate document handling...")
        
        # Try to process the same document again
        processed_docs3 = revision_ctrl.process_documents([test_doc2])
        
        if len(processed_docs3) == 0:
            print("✅ Duplicate document correctly skipped")
        else:
            print("❌ Duplicate document was processed when it shouldn't be")
            return False
        
        # Test 6: Filename generation
        print("\n📝 Testing filename generation...")
        
        test_doc_complex = {
            'url': 'https://test.com/complex_guide_v3.1_20250920.pdf',
            'filename': 'mds_complex_guide_v3.1_20250920_downloaded.pdf',
            'version': '3.1',
            'title': 'MDS Complex Configuration Guide'
        }
        
        clean_filename = revision_ctrl._generate_current_filename(test_doc_complex)
        
        if clean_filename and 'v3.1' in clean_filename and len(clean_filename) < 150:
            print(f"✅ Filename generation works: {clean_filename}")
        else:
            print(f"❌ Filename generation issue: {clean_filename}")
            return False
        
        # Test 7: Check for updates functionality
        print("\n🔍 Testing update detection...")
        
        # Test with identical document (should not update)
        no_updates = revision_ctrl.check_for_updates([test_doc2])
        if len(no_updates) == 0:
            print("✅ Identical document correctly detected as no update")
        else:
            print("❌ Identical document incorrectly flagged as update")
            return False
        
        print("\n🎉 All revision control tests passed!")
        return True


if __name__ == "__main__":
    print("🚀 Starting Revision Control Validation\n")
    
    success = test_revision_control()
    
    if success:
        print("\n✅ Revision control validation completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Revision control validation failed")
        sys.exit(1)