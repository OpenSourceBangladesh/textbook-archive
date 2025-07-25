#!/usr/bin/env python3
"""
Script to retry downloading only the failed PDF files from the previous run
"""

import os
import re
import json
import requests
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading

class RetryFailedDownloader:
    def __init__(self, base_dir="2025", max_workers=2, retry_count=5):
        self.base_dir = Path(base_dir)
        self.max_workers = max_workers
        self.retry_count = retry_count
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        self.newly_downloaded = {}
        self.still_failed = []
        self.lock = threading.Lock()

    def load_previous_results(self):
        """Load the previous download results from index.json"""
        index_path = self.base_dir / "index.json"
        
        if not index_path.exists():
            print("❌ No previous index.json found!")
            return []
        
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        failed_downloads = data.get('failed_downloads', [])
        print(f"📋 Found {len(failed_downloads)} failed downloads from previous run")
        
        return failed_downloads

    def extract_google_drive_id(self, url):
        """Extract file ID from Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_google_drive_download_url(self, file_id):
        """Get direct download URL for Google Drive file with virus scan bypass"""
        # Try different approaches for Google Drive downloads
        return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t"

    def get_egovcloud_download_url(self, url):
        """Convert egovcloud share URL to download URL"""
        if '/index.php/s/' in url:
            return url + '/download'
        return url

    def download_file_advanced(self, url, file_path, book_name, link_num):
        """Advanced download with multiple fallback methods"""
        for attempt in range(self.retry_count):
            try:
                print(f"  🔄 Attempt {attempt + 1}/{self.retry_count}: {book_name} (Link {link_num})")
                
                # Determine download URL based on domain
                if 'drive.google.com' in url:
                    file_id = self.extract_google_drive_id(url)
                    if not file_id:
                        raise Exception(f"Could not extract Google Drive file ID from: {url}")
                    
                    # Try multiple Google Drive download methods
                    download_urls = [
                        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
                        f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
                        f"https://drive.google.com/uc?id={file_id}&export=download",
                        f"https://docs.google.com/uc?export=download&id={file_id}"
                    ]
                    
                    success = False
                    for i, download_url in enumerate(download_urls):
                        try:
                            print(f"    📥 Trying method {i+1}: {download_url[:60]}...")
                            success = self._attempt_download(download_url, file_path, file_id if 'drive.google.com' in url else None)
                            if success:
                                break
                        except Exception as e:
                            print(f"    ❌ Method {i+1} failed: {str(e)[:100]}")
                            continue
                    
                    if not success:
                        raise Exception("All Google Drive download methods failed")
                        
                elif 'drive.egovcloud.gov.bd' in url:
                    download_url = self.get_egovcloud_download_url(url)
                    print(f"    📥 eGovCloud: {download_url}")
                    success = self._attempt_download(download_url, file_path)
                    if not success:
                        raise Exception("eGovCloud download failed")
                else:
                    print(f"    📥 Direct: {url}")
                    success = self._attempt_download(url, file_path)
                    if not success:
                        raise Exception("Direct download failed")

                # If we get here, download was successful
                with self.lock:
                    self.newly_downloaded[str(file_path)] = {
                        'book_name': book_name,
                        'link_number': link_num,
                        'original_url': url,
                        'file_size': file_path.stat().st_size,
                        'download_time': time.time(),
                        'retry_attempt': attempt + 1
                    }

                print(f"  ✅ Success: {book_name} (Link {link_num}) - {file_path.stat().st_size/1024/1024:.1f} MB")
                return True

            except Exception as e:
                error_msg = str(e)[:100]
                print(f"  ❌ Attempt {attempt + 1} failed: {error_msg}")
                if attempt == self.retry_count - 1:
                    with self.lock:
                        self.still_failed.append({
                            'url': url,
                            'file_path': str(file_path),
                            'book_name': book_name,
                            'link_number': link_num,
                            'error': str(e),
                            'retry_attempts': self.retry_count
                        })
                    return False
                else:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + (attempt * 0.5)
                    print(f"  ⏳ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
        
        return False

    def _attempt_download(self, download_url, file_path, google_file_id=None):
        """Attempt to download from a specific URL"""
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Download with streaming
        response = self.session.get(download_url, stream=True, timeout=120, allow_redirects=True)
        
        # Handle Google Drive specific responses
        if google_file_id and response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            
            # Check if it's an HTML page (virus scan warning)
            if 'text/html' in content_type:
                content = response.text
                
                # Look for download confirmation
                if 'virus scan warning' in content.lower() or 'download anyway' in content.lower():
                    # Try to extract the confirm token
                    confirm_patterns = [
                        r'href="[^"]*[?&]confirm=([^&"]+)',
                        r'"downloadUrl":"[^"]*[?&]confirm=([^&"]+)',
                        r'confirm=([a-zA-Z0-9_-]+)'
                    ]
                    
                    for pattern in confirm_patterns:
                        match = re.search(pattern, content)
                        if match:
                            confirm_token = match.group(1)
                            new_url = f"https://drive.usercontent.google.com/download?id={google_file_id}&export=download&confirm={confirm_token}"
                            print(f"    🔄 Using confirm token: {confirm_token}")
                            response = self.session.get(new_url, stream=True, timeout=120)
                            break
                    else:
                        # Try the uuid approach
                        uuid_match = re.search(r'uuid=([^&"]+)', content)
                        if uuid_match:
                            uuid = uuid_match.group(1)
                            new_url = f"https://drive.usercontent.google.com/download?id={google_file_id}&export=download&uuid={uuid}"
                            print(f"    🔄 Using UUID: {uuid}")
                            response = self.session.get(new_url, stream=True, timeout=120)

        response.raise_for_status()

        # Check content type and first bytes
        content_type = response.headers.get('content-type', '').lower()
        content_length = response.headers.get('content-length')
        
        # Get first chunk to check PDF signature
        first_chunk = b''
        chunk_iter = response.iter_content(chunk_size=8192)
        try:
            first_chunk = next(chunk_iter)
        except StopIteration:
            raise Exception("Empty response")

        # Validate it's a PDF
        if not first_chunk.startswith(b'%PDF'):
            # Check if it's HTML error page
            if first_chunk.startswith(b'<!DOCTYPE') or first_chunk.startswith(b'<html'):
                raise Exception("Received HTML page instead of PDF (likely access restricted)")
            else:
                raise Exception(f"Downloaded file is not a PDF. First bytes: {first_chunk[:20]}")

        # Write the file
        with open(file_path, 'wb') as f:
            f.write(first_chunk)
            # Write the rest
            for chunk in chunk_iter:
                if chunk:
                    f.write(chunk)

        # Verify file size
        file_size = file_path.stat().st_size
        if file_size < 1000:  # Less than 1KB
            raise Exception(f"Downloaded file is too small: {file_size} bytes")

        return True

    def retry_failed_downloads(self):
        """Retry downloading all failed files"""
        failed_downloads = self.load_previous_results()
        
        if not failed_downloads:
            print("🎉 No failed downloads to retry!")
            return

        print(f"🚀 Starting retry of {len(failed_downloads)} failed downloads...")
        print("⚠️  Using more aggressive retry strategy with multiple fallback methods")
        
        # Convert failed downloads to proper format
        retry_tasks = []
        for failed in failed_downloads:
            file_path = Path(failed['file_path'])
            retry_tasks.append({
                'url': failed['url'],
                'file_path': file_path,
                'book_name': failed['book_name'],
                'link_number': failed['link_number']
            })

        # Download with reduced concurrency for more reliability
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all retry tasks
            future_to_task = {
                executor.submit(
                    self.download_file_advanced,
                    task['url'],
                    task['file_path'],
                    task['book_name'],
                    task['link_number']
                ): task for task in retry_tasks
            }
            
            # Progress bar
            with tqdm(total=len(retry_tasks), desc="Retrying failed downloads") as pbar:
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        success = future.result()
                        if success:
                            pbar.set_postfix({"✅": "Success"})
                        else:
                            pbar.set_postfix({"❌": "Still failed"})
                    except Exception as e:
                        pbar.set_postfix({"💥": f"Error: {str(e)[:20]}"})
                    
                    pbar.update(1)

    def update_index_json(self):
        """Update the index.json with new results"""
        index_path = self.base_dir / "index.json"
        
        # Load existing data
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update downloaded files
        data['downloaded_files'].update(self.newly_downloaded)
        
        # Update failed downloads (remove successful ones)
        original_failed = data['failed_downloads']
        successful_file_paths = set(self.newly_downloaded.keys())
        
        # Keep only the downloads that are still failing
        data['failed_downloads'] = self.still_failed
        
        # Update statistics
        data['total_downloaded'] = len(data['downloaded_files'])
        data['total_failed'] = len(data['failed_downloads'])
        data['last_retry_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
        data['retry_summary'] = {
            'newly_successful': len(self.newly_downloaded),
            'still_failed': len(self.still_failed),
            'total_size_bytes': sum(info.get('file_size', 0) for info in data['downloaded_files'].values())
        }
        
        # Write updated data
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Updated index.json with retry results")
        return data

    def run(self):
        """Main execution method"""
        print("🔄 Failed Downloads Retry Manager")
        print("=" * 50)
        
        # Retry failed downloads
        self.retry_failed_downloads()
        
        # Update index
        updated_data = self.update_index_json()
        
        # Summary
        print(f"\n📊 Retry Summary:")
        print(f"✅ Newly successful downloads: {len(self.newly_downloaded)}")
        print(f"❌ Still failed: {len(self.still_failed)}")
        print(f"📁 New total successful: {updated_data['total_downloaded']}")
        print(f"📁 New total size: {updated_data['retry_summary']['total_size_bytes'] / (1024*1024):.2f} MB")
        
        if self.newly_downloaded:
            print(f"\n🎉 Successfully downloaded:")
            for file_path, info in self.newly_downloaded.items():
                print(f"  ✅ {info['book_name']} (Link {info['link_number']}) - {info['file_size']/1024/1024:.1f} MB")
        
        if self.still_failed:
            print(f"\n❌ Still failing:")
            for failed in self.still_failed:
                print(f"  ❌ {failed['book_name']} (Link {failed['link_number']}): {failed['error'][:80]}...")
        
        print("\n🎉 Retry process completed!")

def main():
    """Main function"""
    downloader = RetryFailedDownloader(
        base_dir="2025",
        max_workers=2,  # Even more conservative for retries
        retry_count=5   # More retry attempts
    )
    downloader.run()

if __name__ == "__main__":
    main()
