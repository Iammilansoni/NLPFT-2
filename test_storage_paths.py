#!/usr/bin/env python3
"""
Test script to verify storage path configuration.
Run this from the NLPForge-Tester project root to verify paths.
"""

from pathlib import Path
import sys

# Add app directory to Python path
project_root = Path(__file__).parent
app_dir = project_root / "app"
sys.path.insert(0, str(app_dir))

from app.core.config import settings

def test_storage_paths():
    """Test that all storage paths are correctly configured."""
    print("🔍 Testing NLPForge-Tester storage path configuration...")
    print()
    
    # Test project root
    print(f"📁 Project Root: {settings.project_root}")
    print(f"   Exists: {settings.project_root.exists()}")
    print()
    
    # Test storage path
    print(f"📁 Storage Path: {settings.storage_path}")
    print(f"   Exists: {settings.storage_path.exists()}")
    print()
    
    # Test individual file paths
    paths_to_test = [
        ("Function Dictionary", settings.function_dictionary_path),
        ("Feedback Database", settings.feedback_db_path),
        ("FAISS Index Directory", settings.faiss_index_path),
    ]
    
    for name, path in paths_to_test:
        print(f"📄 {name}: {path}")
        print(f"   Exists: {path.exists()}")
        print()
    
    # Ensure directories
    print("🛠️  Ensuring storage directories exist...")
    settings.ensure_storage_directories()
    print("✅ Storage directories ensured!")
    print()
    
    # Verify structure
    print("📋 Final storage structure:")
    if settings.storage_path.exists():
        for item in settings.storage_path.iterdir():
            print(f"   - {item.name}")
    
    print()
    print("✅ Storage path test completed!")

if __name__ == "__main__":
    test_storage_paths()
