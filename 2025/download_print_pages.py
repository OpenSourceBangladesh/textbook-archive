#!/usr/bin/env python3
"""
Script to download print versions of NCTB textbook pages from CSV links
and save them in /csv/[year]/index.html format
"""

import csv
import requests
import os
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from typing import Optional
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NCTBDownloader:
    def __init__(self, csv_file: str = "", output_dir: str = "csv"):
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.session = requests.Session()
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def extract_year_from_title(self, title: str) -> Optional[str]:
        """Extract year from Bengali title"""
        # Look for 4-digit year patterns in Bengali numerals and English
        bengali_to_english = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        
        # Convert Bengali numerals to English
        english_title = title
        for bengali, english in bengali_to_english.items():
            english_title = english_title.replace(bengali, english)
        
        # Look for year patterns (2017-2025)
        year_match = re.search(r'(201[7-9]|202[0-5])', english_title)
        if year_match:
            return year_match.group(1)
        
        # Handle special cases
        if "English for Today" in title:
            return "unknown"
        
        return "unknown"

    def download_page(self, url: str) -> Optional[str]:
        """Download a page and return its content"""
        try:
            # Handle both http and https, try multiple approaches
            urls_to_try = []
            
            if url.startswith('https://'):
                # Try https first, then http fallback
                urls_to_try.append(url)
                urls_to_try.append(url.replace('https://', 'http://'))
            elif url.startswith('http://'):
                # Try http first, then https
                urls_to_try.append(url)
                urls_to_try.append(url.replace('http://', 'https://'))
            else:
                # Add protocol if missing
                urls_to_try.append(f"https://{url}")
                urls_to_try.append(f"http://{url}")
            
            for try_url in urls_to_try:
                try:
                    print(f"  Trying: {try_url}")
                    # Try with SSL verification first
                    response = self.session.get(try_url, timeout=30, verify=True)
                    response.raise_for_status()
                    return response.text
                except requests.exceptions.SSLError:
                    # Try without SSL verification
                    try:
                        print(f"  SSL failed, trying without verification...")
                        response = self.session.get(try_url, timeout=30, verify=False)
                        response.raise_for_status()
                        return response.text
                    except Exception as e2:
                        print(f"  Failed without SSL verification: {e2}")
                        continue
                except Exception as e:
                    print(f"  Failed: {e}")
                    continue
            
            print(f"All attempts failed for URL: {url}")
            return None
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def extract_printable_content(self, html_content: str, original_url: str) -> str:
        """Extract the printable content from the full page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the printable area div
        printable_area = soup.find('div', {'id': 'printable_area'})
        
        if printable_area:
            # Create a clean HTML document with just the printable content
            clean_html = f"""<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8"></head><body>{printable_area}

<style>a:visited span {{
  color: green !important; 
}}
#left-content ul {{
  	list-style: circle;
	list-style-position: inside;
}}
th{{
	border:1px solid black;
}}
td{{
	border:1px solid black;
}}
@media only screen and (min-width:320px) and (max-width:959px){{
  table {{
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }}
  #printable_area p img {{
	width:100%!important;
	height: unset!important;
  }}
}}

sub {{
    vertical-align: sub!important;
    font-size: smaller!important;
}}
</style></body></html>"""
            return clean_html
        else:
            # If no printable area found, try to extract main content
            content_div = soup.find('div', {'id': 'left-content'}) or soup.find('div', class_='content')
            if content_div:
                return f"""<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8"></head><body>{content_div}
</body></html>"""
            else:
                # Fallback: return the body content
                body = soup.find('body')
                if body:
                    return f"""<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8"></head>{body}
</html>"""
                else:
                    return html_content

    def ensure_directory(self, path: str):
        """Create directory if it doesn't exist"""
        os.makedirs(path, exist_ok=True)

    def process_csv(self):
        """Process the CSV file and download all pages"""
        if not os.path.exists(self.csv_file):
            print(f"CSV file {self.csv_file} not found!")
            return

        # Create base output directory
        self.ensure_directory(self.output_dir)

        with open(self.csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                title = row['title'].strip()
                link = row['link'].strip()
                
                print(f"Processing: {title}")
                print(f"URL: {link}")
                
                # Extract year from title
                year = self.extract_year_from_title(title)
                if not year:
                    year = "unknown"
                print(f"Detected year: {year}")
                
                # Create year directory
                year_dir = os.path.join(self.output_dir, year)
                self.ensure_directory(year_dir)
                
                # Download the page
                html_content = self.download_page(link)
                if not html_content:
                    print(f"Failed to download {link}")
                    continue
                
                # Extract printable content
                print_content = self.extract_printable_content(html_content, link)
                
                # Save to index.html in year directory
                output_file = os.path.join(year_dir, 'index.html')
                
                # If file already exists, create numbered versions
                counter = 1
                original_output_file = output_file
                while os.path.exists(output_file):
                    name, ext = os.path.splitext(original_output_file)
                    output_file = f"{name}_{counter}{ext}"
                    counter += 1
                
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(print_content)
                    print(f"Saved: {output_file}")
                except Exception as e:
                    print(f"Error saving {output_file}: {e}")
                
                # Be nice to the server
                time.sleep(2)
                print("-" * 50)

    def download_single_page(self, url: str, folder_path: str, filename: str = "index.html"):
        """Download a single page to specified folder"""
        print(f"Downloading: {url}")
        
        # Create the folder if it doesn't exist
        self.ensure_directory(folder_path)
        
        # Download the page
        html_content = self.download_page(url)
        if not html_content:
            print(f"Failed to download {url}")
            return False
        
        # Extract printable content
        print_content = self.extract_printable_content(html_content, url)
        
        # Create full file path
        output_file = os.path.join(folder_path, filename)
        
        # If file already exists, create numbered versions
        counter = 1
        original_output_file = output_file
        while os.path.exists(output_file):
            name, ext = os.path.splitext(original_output_file)
            output_file = f"{name}_{counter}{ext}"
            counter += 1
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(print_content)
            print(f"Successfully saved: {output_file}")
            return True
        except Exception as e:
            print(f"Error saving {output_file}: {e}")
            return False

def main():
    """Main function for interactive mode"""
    print("=== NCTB Textbook Page Downloader ===")
    print("This script will download print versions of NCTB textbook pages.")
    print("You can specify the URL and folder location for each download.")
    print("Type 'exit' or 'quit' to stop the program.\n")
    
    # Initialize downloader (no CSV file needed for interactive mode)
    downloader = NCTBDownloader("")
    
    while True:
        print("-" * 60)
        try:
            # Get URL from user
            url = input("Enter the URL to download (or 'exit'/'quit' to stop): ").strip()
            
            if url.lower() in ['exit', 'quit', '']:
                print("Goodbye!")
                break
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                if '.' in url:  # Looks like a URL without protocol
                    url = 'https://' + url
                else:
                    print("Invalid URL. Please enter a valid URL.")
                    continue
            
            # Get folder path from user
            folder_path = input("Enter the folder path to save (relative to current directory): ").strip()
            
            if not folder_path:
                print("Folder path cannot be empty.")
                continue
            
            # Get filename (optional)
            filename = input("Enter filename (default: index.html): ").strip()
            if not filename:
                filename = "index.html"
            
            # Ensure filename has .html extension
            if not filename.endswith('.html'):
                filename += '.html'
            
            print("\nStarting download...")
            
            # Download the page
            success = downloader.download_single_page(url, folder_path, filename)
            
            if success:
                print("✓ Download completed successfully!")
            else:
                print("✗ Download failed!")
                
            # Be nice to the server
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

if __name__ == "__main__":
    main()
