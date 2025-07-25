#!/usr/bin/env python3
"""
Script to convert all index.html files in the 2025 folder structure to Markdown tables
while preserving the folder structure.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md

class HTMLToMarkdownConverter:
    def __init__(self, base_dir="2025"):
        self.base_dir = Path(base_dir)
        self.converted_count = 0
        self.error_count = 0

    def extract_table_from_html(self, html_content):
        """Extract and clean the table content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the printable area or main content
        printable_area = soup.find('div', {'id': 'printable_area'})
        if not printable_area:
            printable_area = soup.find('body')
        
        if not printable_area:
            return None
        
        # Find the table
        table = printable_area.find('table')
        if not table:
            return None
        
        # Extract the title (h3)
        title_element = printable_area.find('h3')
        title = title_element.get_text().strip() if title_element else ""
        
        return table, title

    def convert_table_to_markdown(self, table, title=""):
        """Convert HTML table to clean Markdown table"""
        rows = table.find_all('tr')
        if not rows:
            return ""
        
        markdown_lines = []
        
        # Add title if exists
        if title:
            markdown_lines.append(f"# {title}")
            markdown_lines.append("")
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            
            # Extract text content from each cell, handling links
            row_data = []
            for cell in cells:
                # Get all text and links in the cell
                cell_content = ""
                
                # Find all links
                links = cell.find_all('a')
                if links:
                    link_texts = []
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        if href and text:
                            link_texts.append(f"[{text}]({href})")
                    
                    if link_texts:
                        cell_content = "<br>".join(link_texts)  # Use <br> for multiple links in same cell
                    else:
                        cell_content = cell.get_text().strip()
                else:
                    cell_content = cell.get_text().strip()
                
                # Clean up extra whitespace and line breaks
                cell_content = ' '.join(cell_content.split())
                row_data.append(cell_content)
            
            # Create markdown table row
            if row_data:
                markdown_lines.append("| " + " | ".join(row_data) + " |")
                
                # Add header separator after first row
                if i == 0:
                    separator = "| " + " | ".join(["---"] * len(row_data)) + " |"
                    markdown_lines.append(separator)
        
        return "\n".join(markdown_lines)

    def process_html_file(self, html_path):
        """Process a single HTML file and convert to Markdown"""
        try:
            # Read HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract table from HTML
            result = self.extract_table_from_html(html_content)
            if not result:
                print(f"⚠️  No table found in: {html_path}")
                return False
            
            table, title = result
            
            # Convert to Markdown
            markdown_content = self.convert_table_to_markdown(table, title)
            
            if not markdown_content.strip():
                print(f"⚠️  No content extracted from: {html_path}")
                return False
            
            # Create markdown file path (same directory, different extension)
            md_path = html_path.parent / "index.md"
            
            # Write Markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Converted: {html_path} → {md_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {html_path}: {e}")
            return False

    def find_all_html_files(self):
        """Find all index.html files in the directory structure"""
        html_files = []
        for html_file in self.base_dir.rglob("index.html"):
            html_files.append(html_file)
        return html_files

    def convert_all(self):
        """Convert all HTML files to Markdown"""
        print(f"🔍 Searching for index.html files in {self.base_dir}...")
        
        html_files = self.find_all_html_files()
        total_files = len(html_files)
        
        if total_files == 0:
            print("❌ No index.html files found!")
            return
        
        print(f"📁 Found {total_files} index.html files")
        print("🚀 Starting conversion...\n")
        
        for html_file in html_files:
            if self.process_html_file(html_file):
                self.converted_count += 1
            else:
                self.error_count += 1
        
        print(f"\n📊 Conversion Summary:")
        print(f"✅ Successfully converted: {self.converted_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"📁 Total files: {total_files}")

def main():
    """Main function"""
    print("🔄 HTML to Markdown Table Converter")
    print("=" * 50)
    
    # Initialize converter for 2025 directory
    converter = HTMLToMarkdownConverter("2025")
    
    # Check if directory exists
    if not converter.base_dir.exists():
        print(f"❌ Directory {converter.base_dir} not found!")
        return
    
    # Convert all files
    converter.convert_all()
    
    print("\n🎉 Conversion completed!")

if __name__ == "__main__":
    main()
