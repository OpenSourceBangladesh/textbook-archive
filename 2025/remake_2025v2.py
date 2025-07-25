#!/usr/bin/env python3
"""
Remake 2025V2 folder with clean PDF names and single v2index.json
- PDF files: XXX.pdf (not XXX_2.pdf)
- Single v2index.json only
- Clean folder structure
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("🚀 Remaking 2025V2 Folder")
    print("=" * 50)
    
    # Paths
    source_folder = Path("2025")  # Use the main 2025 folder as source
    new_folder = Path("2025V2_new")
    index_file = Path("2025/index.json")
    
    # Read original index
    print("📖 Reading original index.json...")
    with open(index_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Remove existing new folder if it exists
    if new_folder.exists():
        print(f"🗑️ Removing existing {new_folder}...")
        shutil.rmtree(new_folder)
    
    # Create new folder structure
    print(f"📁 Creating new folder structure...")
    new_folder.mkdir(exist_ok=True)
    
    # Process files
    total_files = 0
    total_size = 0
    tree_structure = {}
    copied_files = []
    
    print("🔄 Processing and copying files...")
    
    for file_path, file_info in original_data.get('downloaded_files', {}).items():
        # Only process files with link_number = 2
        if file_info.get('link_number') == 2:
            # Get the original file path in 2025V2
            # Convert path from index format to actual file path
            relative_path = file_path.replace('2025\\', '').replace('2025/', '')
            
            # Check if file exists in 2025V2 (with _2.pdf suffix)
            source_file = source_folder / relative_path
            
            if source_file.exists():
                # Create new filename without _2 suffix
                old_name = source_file.name
                if old_name.endswith('_2.pdf'):
                    new_name = old_name.replace('_2.pdf', '.pdf')
                else:
                    new_name = old_name
                
                # Create target directory structure  
                target_dir = new_folder / source_file.parent.relative_to(source_folder)
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file with new name
                target_file = target_dir / new_name
                shutil.copy2(source_file, target_file)
                
                # Update statistics
                total_files += 1
                file_size = file_info.get('file_size', 0)
                total_size += file_size
                
                # Build tree structure using the relative path from source
                path_parts = str(target_dir.relative_to(new_folder)).replace('\\', '/').split('/')
                if path_parts == ['.']:
                    path_parts = []
                
                # Navigate through folder hierarchy
                current_level = tree_structure
                for part in path_parts:
                    if part and part != '.':
                        if part not in current_level:
                            current_level[part] = {'folders': {}, 'files': {}}
                        current_level = current_level[part]['folders']
                
                # Add file to the appropriate level
                if path_parts and path_parts != ['.']:
                    # Go back to the correct level to add files
                    target_level = tree_structure
                    for part in path_parts[:-1]:
                        if part and part != '.':
                            target_level = target_level[part]['folders']
                    
                    final_folder = path_parts[-1] if path_parts[-1] != '.' else 'root'
                    if final_folder not in target_level:
                        target_level[final_folder] = {'folders': {}, 'files': {}}
                    
                    target_level[final_folder]['files'][new_name] = {
                        'book_name': file_info.get('book_name'),
                        'original_url': file_info.get('original_url'),
                        'file_size': file_size
                    }
                else:
                    # Root level file
                    if 'root' not in tree_structure:
                        tree_structure['root'] = {'folders': {}, 'files': {}}
                    tree_structure['root']['files'][new_name] = {
                        'book_name': file_info.get('book_name'),
                        'original_url': file_info.get('original_url'),
                        'file_size': file_size
                    }
                
                copied_files.append({
                    'old_name': old_name,
                    'new_name': new_name,
                    'path': str(target_dir.relative_to(new_folder)),
                    'size_mb': round(file_size / (1024*1024), 2)
                })
    
    # Create v2index.json
    v2_index = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d'),
            'version': '2.0',
            'description': 'NCTB Textbook Collection - Version 2 (Clean naming)',
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024*1024), 2),
            'naming_convention': 'Clean PDF names (XXX.pdf)'
        },
        'textbooks': tree_structure
    }
    
    # Save v2index.json
    v2_index_path = new_folder / 'v2index.json'
    print("💾 Saving v2index.json...")
    with open(v2_index_path, 'w', encoding='utf-8') as f:
        json.dump(v2_index, f, ensure_ascii=False, indent=2)
    
    # Replace old folder with new one
    print("🔄 Finalizing folder replacement...")
    target_folder = Path("2025V2_clean")
    
    # Remove target if exists
    if target_folder.exists():
        try:
            shutil.rmtree(target_folder)
        except PermissionError:
            target_folder = Path(f"2025V2_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Rename new folder to final target
    new_folder.rename(target_folder)
    
    print(f"✅ New clean folder created: {target_folder}")
    print("💡 You can manually replace the old 2025V2 folder when ready")
    
    # Display results
    print("✅ Remake completed!")
    print(f"📊 Statistics:")
    print(f"   📁 Total files: {total_files}")
    print(f"   📦 Total size: {round(total_size / (1024*1024), 2)} MB")
    print(f"   🎯 Naming: Clean PDF names (XXX.pdf)")
    
    print("🌳 Sample files:")
    for i, file_info in enumerate(copied_files[:5]):
        print(f"   📄 {file_info['old_name']} → {file_info['new_name']} ({file_info['size_mb']} MB)")
    
    if len(copied_files) > 5:
        print(f"   ... and {len(copied_files) - 5} more files")
    
    print("🎉 2025V2 folder remade successfully!")

if __name__ == "__main__":
    main()
