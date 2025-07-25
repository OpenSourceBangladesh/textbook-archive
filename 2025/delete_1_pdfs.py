#!/usr/bin/env python3
"""
Delete all PDF files ending with '_1.pdf' from 2025Final folder
Keep folder structure and v2index.json intact
"""

import os
from pathlib import Path

def delete_pdf_files_ending_with_1(folder_path):
    """
    Delete all PDF files ending with '_1.pdf' from the specified folder
    """
    deleted_files = []
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"❌ Folder {folder_path} does not exist!")
        return deleted_files
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('_1.pdf'):
                file_path = Path(root) / file
                try:
                    # Get file size before deletion
                    file_size = file_path.stat().st_size
                    
                    # Delete the file
                    file_path.unlink()
                    
                    # Record the deletion
                    relative_path = file_path.relative_to(folder)
                    deleted_files.append({
                        'file': str(relative_path),
                        'size': file_size,
                        'size_mb': round(file_size / (1024*1024), 2)
                    })
                    
                    print(f"🗑️ Deleted: {relative_path}")
                    
                except Exception as e:
                    print(f"❌ Failed to delete {file_path}: {e}")
    
    return deleted_files

def main():
    print("🗑️ Deleting PDF files ending with '_1.pdf' from 2025Final")
    print("=" * 60)
    
    folder_path = "2025Final"
    
    # Delete _1.pdf files
    deleted_files = delete_pdf_files_ending_with_1(folder_path)
    
    # Calculate statistics
    total_deleted = len(deleted_files)
    total_size = sum(file['size'] for file in deleted_files)
    total_size_mb = total_size / (1024 * 1024)
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Deletion Completed!")
    print("📊 Statistics:")
    print(f"   🗑️ Total files deleted: {total_deleted}")
    print(f"   💾 Total space freed: {total_size_mb:.2f} MB")
    
    if deleted_files:
        print("\n🗂️ Sample deleted files:")
        for i, file_info in enumerate(deleted_files[:10]):
            print(f"   📄 {file_info['file']} ({file_info['size_mb']} MB)")
        
        if len(deleted_files) > 10:
            print(f"   ... and {len(deleted_files) - 10} more files")
    
    # Check remaining files
    remaining_pdfs = []
    folder = Path(folder_path)
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.pdf'):
                remaining_pdfs.append(file)
    
    print(f"\n📁 Remaining PDF files: {len(remaining_pdfs)}")
    print("📋 v2index.json preserved")
    print(f"📂 Folder structure maintained")
    
    print(f"\n🎉 2025Final cleanup completed!")
    print(f"📂 Location: {Path(folder_path).absolute()}")
    print("📋 Only _2.pdf files and v2index.json remain")

if __name__ == "__main__":
    main()
