#!/usr/bin/env python3
"""
Script to count PDF files with _1.pdf and _2.pdf suffixes in the 2025 directory
"""

import os
from pathlib import Path
from collections import defaultdict

def count_pdf_suffixes(base_dir="2025"):
    """Count PDFs with _1.pdf and _2.pdf suffixes"""
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"❌ Directory {base_dir} does not exist!")
        return
    
    print(f"🔍 Scanning {base_path.absolute()} for PDF files...")
    print("=" * 60)
    
    # Initialize counters
    suffix_counts = defaultdict(int)
    folder_counts = defaultdict(lambda: defaultdict(int))
    total_pdfs = 0
    
    # Find all PDF files recursively
    pdf_files = list(base_path.rglob("*.pdf"))
    total_pdfs = len(pdf_files)
    
    print(f"📁 Total PDF files found: {total_pdfs}")
    print()
    
    # Count by suffix
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        if filename.endswith('_1.pdf'):
            suffix_counts['_1.pdf'] += 1
            # Get the relative folder path
            folder_path = pdf_file.relative_to(base_path).parent
            folder_counts[str(folder_path)]['_1.pdf'] += 1
        elif filename.endswith('_2.pdf'):
            suffix_counts['_2.pdf'] += 1
            folder_path = pdf_file.relative_to(base_path).parent
            folder_counts[str(folder_path)]['_2.pdf'] += 1
        else:
            suffix_counts['other'] += 1
            folder_path = pdf_file.relative_to(base_path).parent
            folder_counts[str(folder_path)]['other'] += 1
    
    # Print summary
    print("📊 Summary by Suffix:")
    print("-" * 30)
    for suffix, count in sorted(suffix_counts.items()):
        percentage = (count / total_pdfs * 100) if total_pdfs > 0 else 0
        print(f"  {suffix:<10}: {count:>4} files ({percentage:>5.1f}%)")
    
    print()
    print("📂 Breakdown by Folder:")
    print("-" * 50)
    
    # Sort folders for better readability
    for folder_path in sorted(folder_counts.keys()):
        counts = folder_counts[folder_path]
        total_in_folder = sum(counts.values())
        
        print(f"\n📁 {folder_path}:")
        print(f"   Total: {total_in_folder} files")
        
        if counts['_1.pdf'] > 0:
            print(f"   _1.pdf: {counts['_1.pdf']} files")
        if counts['_2.pdf'] > 0:
            print(f"   _2.pdf: {counts['_2.pdf']} files")
        if counts['other'] > 0:
            print(f"   other:  {counts['other']} files")
    
    # Check for potential issues
    print()
    print("🔍 Analysis:")
    print("-" * 20)
    
    if suffix_counts['_1.pdf'] == suffix_counts['_2.pdf']:
        print("✅ Equal number of _1.pdf and _2.pdf files - Good!")
    else:
        diff = abs(suffix_counts['_1.pdf'] - suffix_counts['_2.pdf'])
        if suffix_counts['_1.pdf'] > suffix_counts['_2.pdf']:
            print(f"⚠️  More _1.pdf files than _2.pdf files (difference: {diff})")
        else:
            print(f"⚠️  More _2.pdf files than _1.pdf files (difference: {diff})")
    
    if suffix_counts['other'] > 0:
        print(f"⚠️  Found {suffix_counts['other']} files with non-standard naming")
    else:
        print("✅ All PDF files follow the standard naming convention")
    
    # Expected vs actual
    expected_total = 933  # Based on previous summary
    if total_pdfs == expected_total:
        print(f"✅ Total PDF count matches expected ({expected_total})")
    else:
        print(f"⚠️  Total PDF count ({total_pdfs}) differs from expected ({expected_total})")
    
    return suffix_counts, folder_counts, total_pdfs

def main():
    """Main function"""
    print("📊 PDF Suffix Counter")
    print("=" * 60)
    
    suffix_counts, folder_counts, total_pdfs = count_pdf_suffixes()
    
    print(f"\n🎯 Final Summary:")
    print(f"   Total PDFs: {total_pdfs}")
    print(f"   _1.pdf files: {suffix_counts['_1.pdf']}")
    print(f"   _2.pdf files: {suffix_counts['_2.pdf']}")
    print(f"   Other files: {suffix_counts['other']}")

if __name__ == "__main__":
    main()
