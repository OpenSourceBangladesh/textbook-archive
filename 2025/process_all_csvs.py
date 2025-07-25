#!/usr/bin/env python3
"""
Script to process all CSV files from 2017-2025, create UID folders,
and download print versions of NCTB textbook pages
"""

import csv
import requests
import os
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from typing import Optional, List, Dict
import urllib3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NCTBBulkDownloader:
    def __init__(self, base_dir: str = "csv", max_workers: int = 5, max_retries: int = 3):
        self.base_dir = base_dir
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.years = [str(year) for year in range(2017, 2026)]  # 2017-2025
        self.failed_downloads = []
        self.download_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'retried': 0
        }
        self.lock = threading.Lock()

    def create_session(self):
        """Create a new session for each thread"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session

    def should_skip_link(self, url: str) -> bool:
        """Check if the link should be skipped (Google Drive or egovcloud)"""
        skip_domains = [
            'drive.google.com',
            'drive.egovcloud.gov.bd'
        ]
        
        for domain in skip_domains:
            if domain in url.lower():
                return True
        return False

    def read_csv_file(self, csv_path: str) -> List[Dict[str, str]]:
        """Read CSV file and return list of dictionaries"""
        if not os.path.exists(csv_path):
            return []
        
        data = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Handle different column names
                    uid = row.get('UID', '').strip()
                    link = row.get('link', row.get('Link', '')).strip()
                    class_name = row.get('class', row.get('Level', '')).strip()
                    
                    if uid and link and not self.should_skip_link(link):
                        data.append({
                            'UID': uid,
                            'link': link,
                            'class': class_name
                        })
        except Exception as e:
            print(f"Error reading {csv_path}: {e}")
        
        return data

    def create_uid_folders(self):
        """Create UID folders for all years and return the structure"""
        folder_structure = {}
        total_created = 0
        total_existing = 0
        
        for year in self.years:
            csv_path = os.path.join(self.base_dir, year, 'index.csv')
            data = self.read_csv_file(csv_path)
            
            if not data:
                print(f"No data found for year {year}")
                continue
            
            year_folders = []
            year_created = 0
            year_existing = 0
            
            for entry in data:
                uid = entry['UID']
                uid_folder = os.path.join(self.base_dir, year, uid)
                
                # Check if folder already exists
                folder_existed = os.path.exists(uid_folder)
                index_exists = os.path.exists(os.path.join(uid_folder, 'index.html'))
                
                # Create the folder
                os.makedirs(uid_folder, exist_ok=True)
                
                year_folders.append({
                    'uid': uid,
                    'folder': uid_folder,
                    'link': entry['link'],
                    'class': entry['class']
                })
                
                if not folder_existed:
                    print(f"Created folder: {uid_folder}")
                    year_created += 1
                    total_created += 1
                elif index_exists:
                    print(f"Folder exists with index.html: {uid_folder}")
                    year_existing += 1
                    total_existing += 1
                else:
                    print(f"Folder exists (empty): {uid_folder}")
                    year_created += 1
                    total_created += 1
            
            folder_structure[year] = year_folders
            print(f"Year {year}: {year_created} new/empty folders, {year_existing} with existing index.html")
        
        print(f"\nOverall: {total_created} folders to process, {total_existing} already completed")
        return folder_structure

    def download_page(self, url: str, session: Optional[requests.Session] = None) -> Optional[str]:
        """Download a page and return its content"""
        if session is None:
            session = self.create_session()
            
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
                    print(f"    Trying: {try_url}")
                    # Try without SSL verification first
                    response = session.get(try_url, timeout=30, verify=False)
                    response.raise_for_status()
                    return response.text
                except Exception as e1:
                    # Try with SSL verification if no SSL failed
                    try:
                        print(f"    SSL off failed, trying with SSL verification...")
                        response = session.get(try_url, timeout=30, verify=True)
                        response.raise_for_status()
                        return response.text
                    except Exception as e2:
                        print(f"    Failed with SSL verification: {e2}")
                        continue
            
            print(f"    All attempts failed for URL: {url}")
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

    def download_single_item(self, folder_info: Dict, session: requests.Session) -> Dict:
        """Download a single item and return result"""
        uid = folder_info['uid']
        folder_path = folder_info['folder']
        link = folder_info['link']
        class_name = folder_info['class']
        year = folder_info['year']
        
        result = {
            'uid': uid,
            'year': year,
            'class': class_name,
            'link': link,
            'folder_path': folder_path,
            'success': False,
            'error': None
        }
        
        try:
            # Check if index.html already exists
            output_file = os.path.join(folder_path, 'index.html')
            if os.path.exists(output_file):
                print(f"  ⏭️  Skipping {year}/{uid}: index.html already exists")
                result['success'] = True
                result['error'] = "Skipped - file already exists"
                
                with self.lock:
                    self.download_stats['success'] += 1
                
                return result
            
            print(f"  📥 Downloading {year}/{uid}: {class_name}")
            
            # Download the page
            html_content = self.download_page(link, session)
            if not html_content:
                result['error'] = "Failed to download content"
                return result
            
            # Extract printable content
            print_content = self.extract_printable_content(html_content, link)
            
            # Save to index.html in UID folder
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(print_content)
            
            result['success'] = True
            print(f"  ✅ Saved: {year}/{uid}")
            
            with self.lock:
                self.download_stats['success'] += 1
                
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ Error {year}/{uid}: {e}")
            
            with self.lock:
                self.download_stats['failed'] += 1
        
        return result

    def download_batch(self, items: List[Dict], retry_attempt: int = 0) -> List[Dict]:
        """Download a batch of items with threading"""
        failed_items = []
        
        print(f"\n{'='*50}")
        if retry_attempt == 0:
            print(f"Starting batch download of {len(items)} items")
        else:
            print(f"Retry attempt {retry_attempt} for {len(items)} failed items")
        print(f"Using {self.max_workers} concurrent workers")
        print(f"{'='*50}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create a session for each worker
            sessions = [self.create_session() for _ in range(self.max_workers)]
            session_queue = queue.Queue()
            for session in sessions:
                session_queue.put(session)
            
            # Submit all tasks
            future_to_item = {}
            for item in items:
                session = session_queue.get()
                future = executor.submit(self.download_single_item, item, session)
                future_to_item[future] = (item, session)
            
            # Process completed tasks
            for future in as_completed(future_to_item):
                item, session = future_to_item[future]
                session_queue.put(session)  # Return session to queue
                
                try:
                    result = future.result()
                    if not result['success']:
                        failed_items.append(item)
                        if retry_attempt == 0:
                            self.failed_downloads.append(result)
                        
                except Exception as e:
                    print(f"  ❌ Thread error for {item['uid']}: {e}")
                    failed_items.append(item)
                    if retry_attempt == 0:
                        self.failed_downloads.append({
                            'uid': item['uid'],
                            'year': item['year'],
                            'error': f"Thread error: {e}"
                        })
                
                # Small delay between requests
                time.sleep(0.5)
        
        return failed_items

    def download_all_pages(self, folder_structure: Dict):
        """Download pages for all folders with threading and retry"""
        # Prepare all items for download
        all_items = []
        
        for year, folders in folder_structure.items():
            for folder_info in folders:
                folder_info['year'] = year  # Add year to folder info
                all_items.append(folder_info)
        
        self.download_stats['total'] = len(all_items)
        print(f"\nTotal items to download: {len(all_items)}")
        
        # Initial download attempt
        failed_items = self.download_batch(all_items)
        
        # Retry failed downloads
        retry_count = 0
        while failed_items and retry_count < self.max_retries:
            retry_count += 1
            print(f"\n{'='*50}")
            print(f"RETRY ATTEMPT {retry_count}/{self.max_retries}")
            print(f"Retrying {len(failed_items)} failed downloads")
            print(f"{'='*50}")
            
            with self.lock:
                self.download_stats['retried'] += len(failed_items)
            
            failed_items = self.download_batch(failed_items, retry_count)
            
            if failed_items:
                print(f"Still {len(failed_items)} items failed after retry {retry_count}")
                time.sleep(5)  # Wait before next retry
        
        # Final summary
        self.print_final_summary(failed_items)

    def print_final_summary(self, final_failed_items: List[Dict]):
        """Print the final download summary"""
        skipped_count = sum(1 for item in self.failed_downloads if item.get('error') == "Skipped - file already exists")
        actual_downloads = self.download_stats['success'] - skipped_count
        
        print(f"\n{'='*60}")
        print("FINAL DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Total items: {self.download_stats['total']}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Actually downloaded: {actual_downloads}")
        print(f"Failed downloads: {len(final_failed_items)}")
        print(f"Total retry attempts: {self.download_stats['retried']}")
        
        if self.download_stats['total'] > 0:
            success_rate = (self.download_stats['success']/self.download_stats['total']*100)
            print(f"Overall success rate: {success_rate:.1f}%")
            if skipped_count > 0:
                download_rate = (actual_downloads/(self.download_stats['total'] - skipped_count)*100) if (self.download_stats['total'] - skipped_count) > 0 else 100
                print(f"New download success rate: {download_rate:.1f}%")
        
        if final_failed_items:
            print(f"\n{'='*30}")
            print("PERMANENTLY FAILED DOWNLOADS:")
            print(f"{'='*30}")
            for item in final_failed_items:
                print(f"  ❌ {item['year']}/{item['uid']}: {item['class']}")
                print(f"     URL: {item['link']}")
            
            # Save failed items to a file
            failed_file = os.path.join(self.base_dir, 'failed_downloads.txt')
            with open(failed_file, 'w', encoding='utf-8') as f:
                f.write("Failed Downloads Summary\n")
                f.write("=" * 50 + "\n\n")
                for item in final_failed_items:
                    f.write(f"Year: {item['year']}\n")
                    f.write(f"UID: {item['uid']}\n")
                    f.write(f"Class: {item['class']}\n")
                    f.write(f"URL: {item['link']}\n")
                    f.write(f"Folder: {item['folder_path']}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"\nFailed downloads saved to: {failed_file}")
        else:
            if actual_downloads > 0:
                print(f"\n🎉 All {actual_downloads} new downloads completed successfully!")
            else:
                print(f"\n✅ All files already exist - nothing to download!")

    def process_all(self):
        """Main method to process everything"""
        print("Creating UID folders for all years...")
        folder_structure = self.create_uid_folders()
        
        print(f"\n{'='*50}")
        print("FOLDER CREATION SUMMARY")
        print(f"{'='*50}")
        for year, folders in folder_structure.items():
            print(f"Year {year}: {len(folders)} folders created")
        
        total_folders = sum(len(folders) for folders in folder_structure.values())
        print(f"\nTotal folders created: {total_folders}")
        
        if total_folders == 0:
            print("No folders to process. Exiting.")
            return
        
        # Ask for download settings
        print(f"\n{'='*50}")
        print("DOWNLOAD SETTINGS")
        print(f"{'='*50}")
        print(f"Current settings:")
        print(f"  - Concurrent workers: {self.max_workers}")
        print(f"  - Max retry attempts: {self.max_retries}")
        
        # Ask if user wants to change settings
        change_settings = input("\nDo you want to change download settings? (y/N): ").strip().lower()
        if change_settings == 'y':
            try:
                workers = input(f"Enter number of concurrent workers (current: {self.max_workers}): ").strip()
                if workers:
                    self.max_workers = max(1, min(10, int(workers)))
                
                retries = input(f"Enter max retry attempts (current: {self.max_retries}): ").strip()
                if retries:
                    self.max_retries = max(0, min(10, int(retries)))
                    
                print(f"Updated settings:")
                print(f"  - Concurrent workers: {self.max_workers}")
                print(f"  - Max retry attempts: {self.max_retries}")
            except ValueError:
                print("Invalid input. Using default settings.")
        
        # Ask for confirmation before downloading
        response = input(f"\nDo you want to proceed with downloading {total_folders} items? (y/N): ").strip().lower()
        if response == 'y':
            print("\nStarting downloads...")
            self.download_all_pages(folder_structure)
        else:
            print("Download cancelled. Folders have been created.")

def main():
    """Main function"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, 'csv')
    
    if not os.path.exists(base_dir):
        print(f"CSV directory not found: {base_dir}")
        return
    
    # Default settings - can be changed during runtime
    downloader = NCTBBulkDownloader(base_dir, max_workers=3, max_retries=2)
    downloader.process_all()
    print("Process completed!")

if __name__ == "__main__":
    main()
