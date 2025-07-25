#!/usr/bin/env python3
"""
Script to scan all markdown files and count download links
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_markdown_file(md_path):
    """Parse markdown file and extract download links"""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        downloads = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if line.startswith('|') and '[ডাউনলোড' in line and 'https://' in line:
                # Parse table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
                
                if len(cells) >= 3:  # At least serial, book name, and one download column
                    book_name = ""
                    
                    # Find book name (usually in second or third column)
                    for i, cell in enumerate(cells):
                        if cell and not cell.startswith('[') and not cell.isdigit() and '।' not in cell:
                            if 'শ্রেণি' not in cell and 'ডাউনলোড' not in cell and 'ক্রমিক' not in cell:
                                book_name = cell
                                break
                    
                    if not book_name:
                        book_name = f"Unknown_Line_{line_num}"

                    # Extract all download links from all cells
                    link_count_in_row = 0
                    for cell in cells:
                        if '[ডাউনলোড' in cell and 'https://' in cell:
                            # Find all links in this cell
                            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                            matches = re.findall(link_pattern, cell)
                            
                            for link_text, url in matches:
                                if 'https://' in url:
                                    # Determine link number from text
                                    link_num = 1
                                    if 'লিংক-২' in link_text or 'Link-2' in link_text:
                                        link_num = 2
                                    elif 'লিংক-১' in link_text or 'Link-1' in link_text:
                                        link_num = 1
                                    
                                    downloads.append({
                                        'book_name': book_name,
                                        'url': url.strip(),
                                        'link_number': link_num,
                                        'link_text': link_text,
                                        'line_number': line_num
                                    })
                                    link_count_in_row += 1

        return downloads

    except Exception as e:
        print(f"Error parsing {md_path}: {e}")
        return []

def analyze_markdown_files(base_dir="2025"):
    """Analyze all markdown files and count links"""
    base_path = Path(base_dir)
    
    print("🔍 Scanning for markdown files...")
    md_files = list(base_path.rglob("index.md"))
    print(f"📁 Found {len(md_files)} markdown files")
    print("=" * 80)
    
    total_links = 0
    total_books = 0
    folder_stats = defaultdict(lambda: {'files': 0, 'books': 0, 'links': 0, 'link_1': 0, 'link_2': 0})
    all_downloads = []
    
    for md_path in sorted(md_files):
        relative_path = md_path.relative_to(base_path)
        folder_path = str(relative_path.parent) if relative_path.parent.name != '2025' else 'root'
        
        print(f"\n📂 {relative_path}")
        print("-" * 60)
        
        downloads = parse_markdown_file(md_path)
        
        if not downloads:
            print("   ⚠️  No download links found")
            continue
        
        # Count stats for this file
        books_in_file = set()
        link_1_count = 0
        link_2_count = 0
        
        for download in downloads:
            books_in_file.add(download['book_name'])
            all_downloads.append(download)
            
            if download['link_number'] == 1:
                link_1_count += 1
            elif download['link_number'] == 2:
                link_2_count += 1
        
        file_total_links = len(downloads)
        file_total_books = len(books_in_file)
        
        print(f"   📚 Books: {file_total_books}")
        print(f"   🔗 Total links: {file_total_links}")
        print(f"   📎 Link-1: {link_1_count}")
        print(f"   📎 Link-2: {link_2_count}")
        
        # Update folder stats
        folder_stats[folder_path]['files'] += 1
        folder_stats[folder_path]['books'] += file_total_books
        folder_stats[folder_path]['links'] += file_total_links
        folder_stats[folder_path]['link_1'] += link_1_count
        folder_stats[folder_path]['link_2'] += link_2_count
        
        # Update totals
        total_links += file_total_links
        total_books += file_total_books
        
        # Show some example books
        if file_total_books > 0:
            print(f"   📖 Sample books:")
            for i, book in enumerate(sorted(books_in_file)[:3]):
                print(f"      {i+1}. {book}")
            if file_total_books > 3:
                print(f"      ... and {file_total_books - 3} more")
    
    # Summary by folder
    print(f"\n{'='*80}")
    print("📊 SUMMARY BY FOLDER")
    print(f"{'='*80}")
    
    for folder, stats in sorted(folder_stats.items()):
        print(f"\n📁 {folder}")
        print(f"   Files: {stats['files']}")
        print(f"   Books: {stats['books']}")
        print(f"   Links: {stats['links']} (Link-1: {stats['link_1']}, Link-2: {stats['link_2']})")
    
    # Overall summary
    print(f"\n{'='*80}")
    print("🎯 OVERALL SUMMARY")
    print(f"{'='*80}")
    
    unique_books = set(d['book_name'] for d in all_downloads)
    link_1_total = sum(1 for d in all_downloads if d['link_number'] == 1)
    link_2_total = sum(1 for d in all_downloads if d['link_number'] == 2)
    
    print(f"📁 Total markdown files: {len(md_files)}")
    print(f"📚 Total unique books: {len(unique_books)}")
    print(f"🔗 Total download links: {total_links}")
    print(f"📎 Link-1 count: {link_1_total}")
    print(f"📎 Link-2 count: {link_2_total}")
    print(f"⚖️  Balance: {abs(link_1_total - link_2_total)} difference")
    
    # Domain analysis
    domains = defaultdict(int)
    for download in all_downloads:
        url = download['url']
        if 'drive.google.com' in url:
            domains['Google Drive'] += 1
        elif 'drive.egovcloud.gov.bd' in url:
            domains['eGovCloud'] += 1
        else:
            domains['Other'] += 1
    
    print(f"\n📡 Links by domain:")
    for domain, count in sorted(domains.items()):
        percentage = (count / total_links) * 100
        print(f"   {domain}: {count} links ({percentage:.1f}%)")
    
    # Expected vs actual check
    expected_from_scan = total_links
    print(f"\n✅ Expected PDFs to download: {expected_from_scan}")
    
    return all_downloads, folder_stats

def main():
    """Main function"""
    print("📋 Markdown Link Counter")
    print("=" * 80)
    
    downloads, stats = analyze_markdown_files("2025")
    
    print(f"\n🎉 Scan completed!")
    print(f"📊 Found {len(downloads)} total download links across all markdown files")

if __name__ == "__main__":
    main()
