#!/usr/bin/env python3
"""
Script to create v2index.json with tree structure containing only _2.pdf files
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def create_v2_index():
    """Create v2index.json with tree structure for _2.pdf files only"""
    
    # Read the original index
    print("📖 Reading original index.json...")
    with open('2025V2/index.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Initialize tree structure
    tree_structure = {}
    total_files = 0
    total_size = 0
    
    print("🔄 Processing files...")
    
    # Process downloaded files
    for file_path, file_info in original_data.get('downloaded_files', {}).items():
        # Only include files with link_number = 2
        if file_info.get('link_number') == 2:
            total_files += 1
            total_size += file_info.get('file_size', 0)
            
            # Clean the file info - keep only essential data
            clean_file_info = {
                'book_name': file_info.get('book_name'),
                'link_number': file_info.get('link_number'),
                'original_url': file_info.get('original_url'),
                'file_size': file_info.get('file_size')
            }
            
            # Parse the file path to build tree structure
            # Remove the base "2025\\" part and normalize path separators
            relative_path = file_path.replace('2025\\\\', '').replace('2025\\', '')
            path_parts = relative_path.replace('\\\\', '/').replace('\\', '/').split('/')
            
            # Build nested structure based on education level hierarchy
            current_level = tree_structure
            
            # Navigate through folder levels (skip the last "PDFs" folder and filename)
            folder_parts = [part for part in path_parts[:-1] if part != 'PDFs']  # Remove PDFs folder
            filename = path_parts[-1]
            
            # Build the hierarchy: education_level -> curriculum -> grade -> files
            for part in folder_parts:
                if part not in current_level:
                    current_level[part] = {'folders': {}, 'files': {}}
                current_level = current_level[part]['folders']
            
            # Add the file directly to the current level (no extra PDFs folder)
            if folder_parts:
                # Go back to the parent level to add files
                target_level = tree_structure
                for part in folder_parts[:-1]:
                    target_level = target_level[part]['folders']
                
                # Add to the final folder
                final_folder = folder_parts[-1]
                if final_folder not in target_level:
                    target_level[final_folder] = {'folders': {}, 'files': {}}
                
                target_level[final_folder]['files'][filename] = clean_file_info
            else:
                # If no folder structure, add to root
                if 'root' not in tree_structure:
                    tree_structure['root'] = {'folders': {}, 'files': {}}
                tree_structure['root']['files'][filename] = clean_file_info
    
    # Create the final v2 index structure
    v2_index = {
        'metadata': {
            'generated_at': '2025-07-20',
            'version': '2.0',
            'description': 'NCTB Textbook Collection - Version 2 (Link 2 only)',
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'filter_criteria': 'Only PDFs with link_number = 2 (_2.pdf files)'
        },
        'textbooks': tree_structure
    }
    
    # Save the new v2index.json
    output_path = '2025V2/v2index.json'
    print(f"💾 Saving v2index.json...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(v2_index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Created {output_path}")
    print(f"📊 Statistics:")
    print(f"   📁 Total files: {total_files}")
    print(f"   📦 Total size: {v2_index['metadata']['total_size_mb']} MB")
    print(f"   🎯 Filter: Only _2.pdf files")
    
    # Display some tree structure examples
    print(f"\n🌳 Sample tree structure:")
    sample_count = 0
    def show_sample(structure, level=0, max_samples=5):
        nonlocal sample_count
        if sample_count >= max_samples:
            return
            
        indent = "  " * level
        for folder_name, folder_data in structure.items():
            if sample_count >= max_samples:
                break
            print(f"{indent}📁 {folder_name}")
            
            # Show files in this folder
            files = folder_data.get('files', {})
            for file_name in list(files.keys())[:2]:  # Show max 2 files per folder
                if sample_count >= max_samples:
                    break
                file_info = files[file_name]
                size_mb = file_info.get('file_size', 0) / (1024 * 1024)
                print(f"{indent}  📄 {file_name} ({size_mb:.1f} MB)")
                sample_count += 1
            
            # Recursively show subfolders
            subfolders = folder_data.get('folders', {})
            if subfolders and sample_count < max_samples:
                show_sample(subfolders, level + 1, max_samples)
    
    show_sample(tree_structure)
    
    if total_files > 5:
        print(f"   ... and {total_files - sample_count} more files")
    
    return v2_index

if __name__ == "__main__":
    print("🚀 V2 Index Generator")
    print("=" * 50)
    create_v2_index()
    print("🎉 V2 index generation completed!")
