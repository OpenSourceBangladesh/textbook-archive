#!/usr/bin/env python3
"""
Create 2025Final folder with:
1. Copy only PDFs and folder structure from 2025 folder
2. Copy v2index.json from 2025V2 folder
3. Maintain exact folder structure but exclude non-PDF files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def copy_pdfs_only(source_dir, target_dir):
    """
    Recursively copy only PDF files and their folder structure
    """
    copied_files = []
    
    for root, dirs, files in os.walk(source_dir):
        # Create relative path from source
        rel_path = os.path.relpath(root, source_dir)
        
        # Create corresponding directory in target
        if rel_path == '.':
            target_root = target_dir
        else:
            target_root = target_dir / rel_path
            target_root.mkdir(parents=True, exist_ok=True)
        
        # Copy only PDF files
        for file in files:
            if file.lower().endswith('.pdf'):
                source_file = Path(root) / file
                target_file = target_root / file
                
                try:
                    shutil.copy2(source_file, target_file)
                    copied_files.append({
                        'source': str(source_file),
                        'target': str(target_file),
                        'size': source_file.stat().st_size
                    })
                    print(f"✅ Copied: {rel_path}/{file}")
                except Exception as e:
                    print(f"❌ Failed to copy {source_file}: {e}")
    
    return copied_files

def main():
    print("🚀 Creating 2025Final Folder")
    print("=" * 60)
    
    # Define paths
    source_folder = Path("2025")
    target_folder = Path("2025Final")
    v2index_source = Path("2025V2/v2index.json")
    
    # Check if source folders exist
    if not source_folder.exists():
        print(f"❌ Source folder {source_folder} does not exist!")
        return
    
    if not v2index_source.exists():
        print(f"❌ v2index.json not found at {v2index_source}!")
        return
    
    # Remove target folder if it exists
    if target_folder.exists():
        print(f"🗑️ Removing existing {target_folder}...")
        shutil.rmtree(target_folder)
    
    # Create target folder
    print(f"📁 Creating {target_folder}...")
    target_folder.mkdir(exist_ok=True)
    
    # Copy PDFs and folder structure
    print("📄 Copying PDFs and folder structure...")
    copied_files = copy_pdfs_only(source_folder, target_folder)
    
    # Copy v2index.json
    print("📋 Copying v2index.json...")
    target_index = target_folder / "v2index.json"
    shutil.copy2(v2index_source, target_index)
    print(f"✅ Copied: v2index.json")
    
    # Calculate statistics
    total_size = sum(file['size'] for file in copied_files)
    total_size_mb = total_size / (1024 * 1024)
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ 2025Final Creation Completed!")
    print("📊 Statistics:")
    print(f"   📁 Total PDF files: {len(copied_files)}")
    print(f"   📦 Total size: {total_size_mb:.2f} MB")
    print(f"   📋 Index file: v2index.json")
    
    # Show sample files
    print("\n🌳 Sample copied files:")
    for i, file_info in enumerate(copied_files[:10]):
        rel_path = os.path.relpath(file_info['target'], target_folder)
        size_mb = file_info['size'] / (1024 * 1024)
        print(f"   📄 {rel_path} ({size_mb:.2f} MB)")
    
    if len(copied_files) > 10:
        print(f"   ... and {len(copied_files) - 10} more files")
    
    print(f"\n🎉 2025Final folder created successfully!")
    print(f"📂 Location: {target_folder.absolute()}")
    print("📋 Contains: PDFs + folder structure + v2index.json")

if __name__ == "__main__":
    main()
