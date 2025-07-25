#!/usr/bin/env python3
"""
Script to download remaining PDFs by scanning markdown files directly
Skips existing files and follows established naming convention
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

class DirectPDFDownloader:
    def __init__(self, base_dir="2025", max_workers=3, retry_count=2):
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
        self.downloaded_files = {}
        self.failed_downloads = []
        self.skipped_files = 0
        self.newly_downloaded = 0
        self.existing_files = 0
        self.lock = threading.Lock()

    def normalize_filename(self, filename):
        """Normalize Bengali filename for safe file system usage"""
        # Remove special characters and normalize
        filename = filename.strip()
        # Replace problematic characters
        replacements = {
            '?': '',
            '/': '_',
            '\\': '_',
            ':': '_',
            '*': '_',
            '"': '',
            '<': '_',
            '>': '_',
            '|': '_',
            '\n': '_',
            '\r': '_',
            '\t': '_'
        }
        
        for old, new in replacements.items():
            filename = filename.replace(old, new)
        
        # Remove extra spaces and normalize
        filename = ' '.join(filename.split())
        return filename

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
        """Get direct download URL for Google Drive file"""
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    def get_egovcloud_download_url(self, url):
        """Convert egovcloud share URL to download URL"""
        if '/index.php/s/' in url:
            return url + '/download'
        return url

    def check_existing_file(self, file_path):
        """Check if file already exists and is valid"""
        if not file_path.exists():
            return False
        
        try:
            # Verify it's a valid PDF
            with open(file_path, 'rb') as f:
                first_bytes = f.read(4)
                if first_bytes == b'%PDF' and file_path.stat().st_size > 1000:
                    return True
                else:
                    print(f"🗑️  Invalid existing file detected: {file_path.name}")
                    file_path.unlink()  # Remove invalid file
                    return False
        except Exception as e:
            print(f"⚠️  Error checking existing file {file_path.name}: {e}")
            try:
                file_path.unlink()  # Remove problematic file
            except:
                pass
            return False

    def download_file(self, url, file_path, book_name, link_num):
        """Download a single file with retry mechanism"""
        # Check if file already exists and is valid
        if self.check_existing_file(file_path):
            print(f"⏭️  Skipping existing file: {file_path.name}")
            with self.lock:
                self.existing_files += 1
                self.downloaded_files[str(file_path)] = {
                    'book_name': book_name,
                    'link_number': link_num,
                    'original_url': url,
                    'file_size': file_path.stat().st_size,
                    'status': 'existing_file'
                }
            return True

        for attempt in range(self.retry_count):
            try:
                print(f"🔄 Attempt {attempt + 1}/{self.retry_count}: {book_name} (Link {link_num})")
                
                # Determine download URL based on domain
                if 'drive.google.com' in url:
                    file_id = self.extract_google_drive_id(url)
                    if not file_id:
                        raise Exception(f"Could not extract Google Drive file ID from: {url}")
                    download_url = self.get_google_drive_download_url(file_id)
                elif 'drive.egovcloud.gov.bd' in url:
                    download_url = self.get_egovcloud_download_url(url)
                else:
                    download_url = url

                # Create directory if it doesn't exist
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Download with streaming
                response = self.session.get(download_url, stream=True, timeout=60)
                
                # Handle Google Drive virus scan warning
                if 'drive.google.com' in download_url and response.status_code == 200:
                    if 'text/html' in response.headers.get('content-type', ''):
                        # Try to find the actual download link in the response
                        content = response.text
                        if 'confirm=' in content:
                            confirm_match = re.search(r'confirm=([^&]+)', content)
                            if confirm_match:
                                confirm_token = confirm_match.group(1)
                                download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                                response = self.session.get(download_url, stream=True, timeout=60)

                response.raise_for_status()

                # Check if it's actually a PDF
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
                    # Check first few bytes for PDF signature
                    first_chunk = next(response.iter_content(chunk_size=8192))
                    if not first_chunk.startswith(b'%PDF'):
                        raise Exception(f"Downloaded file is not a PDF. Content-Type: {content_type}")
                    
                    # Write the first chunk
                    with open(file_path, 'wb') as f:
                        f.write(first_chunk)
                        # Write the rest
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                else:
                    # Normal download
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                # Verify file size
                if file_path.stat().st_size < 1000:  # Less than 1KB might be an error page
                    raise Exception(f"Downloaded file is too small: {file_path.stat().st_size} bytes")

                with self.lock:
                    self.newly_downloaded += 1
                    self.downloaded_files[str(file_path)] = {
                        'book_name': book_name,
                        'link_number': link_num,
                        'original_url': url,
                        'file_size': file_path.stat().st_size,
                        'download_time': time.time(),
                        'status': 'newly_downloaded',
                        'attempt': attempt + 1
                    }

                print(f"  ✅ Success: {book_name} (Link {link_num}) - {file_path.stat().st_size / (1024*1024):.1f} MB")
                return True

            except Exception as e:
                print(f"  ❌ Attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt == self.retry_count - 1:
                    with self.lock:
                        self.failed_downloads.append({
                            'url': url,
                            'file_path': str(file_path),
                            'book_name': book_name,
                            'link_number': link_num,
                            'error': str(e),
                            'attempts': attempt + 1
                        })
                    print(f"  ❌ Final failure: {book_name} (Link {link_num})")
                    return False
                else:
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)  # Exponential backoff with cap
        
        return False

    def parse_markdown_file(self, md_path):
        """Parse markdown file and extract download links"""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            downloads = []
            lines = content.split('\n')
            
            for line in lines:
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
                            continue

                        # Extract all download links from all cells
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
                                            'link_number': link_num
                                        })

            return downloads

        except Exception as e:
            print(f"Error parsing {md_path}: {e}")
            return []

    def scan_all_markdown_files(self):
        """Scan all markdown files and create download tasks"""
        print("🔍 Scanning markdown files for download links...")
        
        md_files = list(self.base_dir.rglob("index.md"))
        print(f"📁 Found {len(md_files)} markdown files")
        
        all_downloads = []
        
        for md_path in md_files:
            relative_path = md_path.relative_to(self.base_dir)
            print(f"📂 Processing: {relative_path}")
            
            # Parse downloads from this file
            downloads = self.parse_markdown_file(md_path)
            
            if not downloads:
                print(f"   ⚠️  No download links found")
                continue
            
            print(f"   📊 Found {len(downloads)} download links")
            
            for download in downloads:
                pdf_dir = md_path.parent / "PDFs"
                normalized_name = self.normalize_filename(download['book_name'])
                filename = f"{normalized_name}_{download['link_number']}.pdf"
                file_path = pdf_dir / filename
                
                all_downloads.append({
                    'url': download['url'],
                    'file_path': file_path,
                    'book_name': download['book_name'],
                    'link_number': download['link_number'],
                    'md_path': md_path
                })
        
        return all_downloads

    def download_all_pdfs(self, downloads):
        """Download all PDFs using thread pool"""
        
        total_files = len(downloads)
        print(f"\n🚀 Starting download process...")
        print(f"📊 Total download links found: {total_files}")
        
        # Check existing files first
        existing_count = 0
        files_to_download = []
        
        print(f"\n🔍 Checking for existing files...")
        for download in downloads:
            if self.check_existing_file(download['file_path']):
                existing_count += 1
                self.existing_files += 1
                self.downloaded_files[str(download['file_path'])] = {
                    'book_name': download['book_name'],
                    'link_number': download['link_number'],
                    'original_url': download['url'],
                    'file_size': download['file_path'].stat().st_size,
                    'status': 'existing_file'
                }
            else:
                files_to_download.append(download)
        
        print(f"✅ Found {existing_count} existing valid PDF files")
        print(f"🔄 Need to download: {len(files_to_download)} files")
        
        if not files_to_download:
            print("🎉 All files already exist! No downloads needed.")
            return
        
        print(f"\n📥 Starting downloads...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_download = {
                executor.submit(
                    self.download_file, 
                    download['url'], 
                    download['file_path'],
                    download['book_name'],
                    download['link_number']
                ): download for download in files_to_download
            }
            
            # Progress bar
            with tqdm(total=len(files_to_download), desc="Downloading PDFs") as pbar:
                for future in as_completed(future_to_download):
                    download = future_to_download[future]
                    try:
                        success = future.result()
                        if success:
                            pbar.set_postfix({"✅": "Success"})
                        else:
                            pbar.set_postfix({"❌": "Failed"})
                    except Exception as e:
                        pbar.set_postfix({"💥": f"Error: {str(e)[:20]}"})
                    
                    pbar.update(1)

    def save_download_report(self):
        """Save comprehensive download report"""
        report_data = {
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_found": len(self.downloaded_files) + len(self.failed_downloads),
            "existing_files": self.existing_files,
            "newly_downloaded": self.newly_downloaded,
            "total_successful": len(self.downloaded_files),
            "total_failed": len(self.failed_downloads),
            "downloaded_files": self.downloaded_files,
            "failed_downloads": self.failed_downloads,
            "statistics": {
                "total_size_bytes": sum(info.get('file_size', 0) for info in self.downloaded_files.values()),
                "retry_count_used": self.retry_count,
                "max_workers_used": self.max_workers
            }
        }
        
        report_path = self.base_dir / "download_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Download report saved: {report_path}")
        return report_data

    def run(self):
        """Main execution method"""
        print("🚀 Direct PDF Downloader (Markdown-based)")
        print("=" * 60)
        print("🎯 Downloading remaining PDFs by scanning markdown files directly")
        print("⚠️  Will skip existing files and preserve all existing content")
        print("=" * 60)
        
        # Scan all markdown files
        downloads = self.scan_all_markdown_files()
        
        if not downloads:
            print("❌ No download links found in markdown files!")
            return
        
        # Download all PDFs
        self.download_all_pdfs(downloads)
        
        # Save report
        report_data = self.save_download_report()
        
        # Summary
        total_files = len(self.downloaded_files)
        total_found = len(downloads)
        
        print(f"\n{'='*60}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"📁 Total links found: {total_found}")
        print(f"✅ Total successful: {total_files}")
        print(f"📂 Existing files: {self.existing_files}")
        print(f"🔄 Newly downloaded: {self.newly_downloaded}")
        print(f"❌ Failed downloads: {len(self.failed_downloads)}")
        print(f"📁 Total size: {report_data['statistics']['total_size_bytes'] / (1024*1024):.2f} MB")
        
        if self.failed_downloads:
            print(f"\n❌ Failed Downloads:")
            for failed in self.failed_downloads[:10]:  # Show first 10
                print(f"  - {failed['book_name']} (Link {failed['link_number']}): {failed['error'][:80]}")
            if len(self.failed_downloads) > 10:
                print(f"  ... and {len(self.failed_downloads) - 10} more")
        
        success_rate = (total_files / total_found) * 100 if total_found else 0
        print(f"\n🎯 Success rate: {success_rate:.1f}%")
        print("🎉 Direct download process completed!")

def main():
    """Main function"""
    downloader = DirectPDFDownloader(
        base_dir="2025",
        max_workers=3,  # Conservative to avoid rate limiting
        retry_count=2   # 2 attempts as requested
    )
    downloader.run()

if __name__ == "__main__":
    main()
