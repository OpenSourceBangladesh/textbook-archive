#!/usr/bin/env python3
"""
FINAL PRODUCTION UPLOAD SCRIPT
Upload NCTB textbook PDFs to Archive.org with proper Bengali title encoding
"""

import json
import os
import requests
import urllib.parse
import time
import tempfile
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Archive.org credentials
ACCESS_KEY = os.getenv('key')
SECRET_KEY = os.getenv('secret')

if not ACCESS_KEY or not SECRET_KEY:
    print("Error: Missing Archive.org credentials in .env.local")
    exit(1)

# Configuration
JSON_FILE = "2025Final/2025.json"
LOCAL_PDF_BASE = "2025Final"
COLLECTION = "opensource"

def encode_for_header(text):
    """Encode UTF-8 text safely for HTTP headers"""
    try:
        # Encode to UTF-8 bytes, then decode as latin-1 for header transmission
        # Archive.org will properly decode this back to UTF-8
        return text.encode('utf-8').decode('latin-1')
    except:
        # Fallback: use ASCII-safe version
        return text.encode('ascii', 'ignore').decode('ascii')

def generate_item_identifier(book_name, level, grade=None, stream=None):
    """Generate a unique identifier for Archive.org item"""
    # Clean the book name for use in identifier
    clean_name = book_name.replace(" ", "-").replace("(", "").replace(")", "")
    clean_name = clean_name.replace("ও", "o").replace("।", "")
    
    # Transliterate common Bengali words to English
    transliterations = {
        "সাহিত্যপাঠ": "sahityapath",
        "সহপাঠ": "sahpaath", 
        "তথ্য": "tothyo",
        "যোগাযোগ": "jogajog",
        "প্রযুক্তি": "projukti",
        "ইংলিশ": "english",
        "ভার্সন": "version",
        "আমার": "amar",
        "বাংলা": "bangla",
        "বই": "boi",
        "গণিত": "gonit",
        "প্রাথমিক": "prathomik",
        "বিজ্ঞান": "biggan",
        "বাংলাদেশ": "bangladesh",
        "বিশ্বপরিচয়": "bishwaporichoy",
        "ইসলাম": "islam",
        "শিক্ষা": "shikkha",
        "হিন্দুধর্ম": "hindudhorm",
        "বৌদ্ধধর্ম": "buddhdhorm",
        "খ্রিষ্টধর্ম": "khrishtodhorm",
        "চারুপাঠ": "charupath",
        "আনন্দপাঠ": "anandapath",
        "সপ্তবর্ণা": "saptoborna",
        "সাহিত্য": "sahitya",
        "কণিকা": "konika",
        "ব্যাকরণ": "byakaron",
        "নির্মিতি": "nirmiti",
        "English": "english",
        "For": "for",
        "Today": "today",
        "Grammar": "grammar",
        "Composition": "composition"
    }
    
    for bengali, english in transliterations.items():
        clean_name = clean_name.replace(bengali, english)
    
    # Remove any remaining non-ASCII characters
    clean_name = ''.join(c for c in clean_name if ord(c) < 128)
    clean_name = clean_name.replace("--", "-").strip("-")
    
    # Build identifier
    parts = ["nctb", level]
    if grade:
        parts.append(f"grade{grade}")
    if stream:
        parts.append(stream)
    parts.append(clean_name)
    
    # Join and clean up
    identifier = "-".join(parts).lower()
    identifier = identifier.replace("--", "-").strip("-")
    
    return identifier

def find_local_pdf_file(filename, level, folder_path=""):
    """Find the local PDF file for upload"""
    
    # Build the local path
    local_path = Path(LOCAL_PDF_BASE) / level
    if folder_path:
        local_path = local_path / folder_path.replace("/", os.sep)
    local_path = local_path / "PDFs"
    
    # Try different filename variations
    base_name = filename.replace(".pdf", "")
    candidates = [
        local_path / filename,
        local_path / f"{base_name}_2.pdf",
        local_path / f"{base_name} _2.pdf",
        local_path / f"{base_name.strip()}_2.pdf"
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    
    return None

def download_pdf_if_needed(original_url, filename, level, folder_path=""):
    """Download PDF from original URL if local file not found"""
    
    download_url = original_url + "/download"
    
    try:
        print(f"  📥 Downloading from: {download_url}")
        
        # Use HEAD to check file size first
        head_response = requests.head(download_url, timeout=30)
        if head_response.status_code == 200:
            content_length = head_response.headers.get('Content-Length')
            if content_length:
                print(f"  📏 Expected file size: {int(content_length):,} bytes")
        
        # Download with streaming
        response = requests.get(download_url, timeout=120, stream=True)
        
        if response.status_code != 200:
            print(f"  ✗ Download failed: {response.status_code}")
            return None
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        total_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                total_size += len(chunk)
        
        temp_file.close()
        
        print(f"  ✓ Downloaded {total_size:,} bytes to temporary file")
        return temp_file.name
        
    except Exception as e:
        print(f"  ✗ Download error: {str(e)}")
        return None

def upload_pdf_to_archive(file_path, identifier, book_name, level, grade=None, stream=None):
    """Upload PDF file to Archive.org using S3 API with proper Bengali encoding"""
    
    print(f"  📤 Uploading to Archive.org...")
    print(f"  🏷️  Item identifier: {identifier}")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    print(f"  📏 File size: {file_size:,} bytes")
    
    # Generate upload filename
    upload_filename = f"{book_name.replace(' ', '_')}.pdf"
    
    # Archive.org S3 URL
    s3_url = f"https://s3.us.archive.org/{identifier}/{upload_filename}"
    
    # Encode Bengali text properly for HTTP headers
    title_encoded = encode_for_header(book_name)
    description_encoded = encode_for_header(f'NCTB textbook: {book_name}')
    
    print(f"  📝 Original title: {book_name}")
    print(f"  🔧 Encoded for headers: {title_encoded}")
    
    # Prepare headers with proper encoding
    headers = {
        'authorization': f'LOW {ACCESS_KEY}:{SECRET_KEY}',
        'Content-Type': 'application/pdf',
        'Content-Length': str(file_size),
        'x-archive-auto-make-bucket': '1',
        'x-archive-meta-collection': COLLECTION,
        'x-archive-meta-mediatype': 'texts',
        'x-archive-meta-title': title_encoded,
        'x-archive-meta-creator': 'National Curriculum and Textbook Board (NCTB), Bangladesh',
        'x-archive-meta-language': 'ben',
        'x-archive-meta-subject': 'education;textbook;bangladesh;nctb',
        'x-archive-meta-description': description_encoded,
        'x-archive-meta-publisher': 'National Curriculum and Textbook Board (NCTB)',
        'x-archive-meta-rights': 'Public Domain',
        'x-archive-meta-level': level,
    }
    
    if grade:
        headers['x-archive-meta-grade'] = str(grade)
    if stream:
        headers['x-archive-meta-stream'] = stream
    
    try:
        # Read file and upload
        print(f"  📖 Reading file...")
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        print(f"  🚀 Uploading {len(file_data):,} bytes...")
        
        # Upload to Archive.org
        response = requests.put(
            s3_url,
            data=file_data,
            headers=headers,
            timeout=300  # 5 minute timeout
        )
        
        print(f"  📊 Response status: {response.status_code}")
        if response.text.strip():
            print(f"  📄 Response: {response.text[:200]}...")
        
        if response.status_code in [200, 201]:
            archive_url = f"https://archive.org/details/{identifier}"
            print(f"  ✅ Upload successful! Archive URL: {archive_url}")
            return archive_url
        else:
            print(f"  ❌ Upload failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Upload error: {str(e)}")
        return None

def update_json_file(json_data, level, folder_path, filename, archive_url):
    """Update the JSON file with the archive URL"""
    
    def update_nested_dict(data, path_parts, file_key, url):
        current = data
        for part in path_parts:
            current = current[part]
        
        if file_key in current:
            current[file_key]["archive_url"] = url
            return True
        return False
    
    # Build path for nested structure
    path_parts = ["textbooks", level]
    
    if folder_path:
        folder_parts = folder_path.split("/")
        for part in folder_parts:
            path_parts.extend(["folders", part])
        path_parts.append("files")
    else:
        path_parts.append("files")
    
    success = update_nested_dict(json_data, path_parts, filename, archive_url)
    return success

def process_files_recursively(json_data, level, folder_path=""):
    """Process files recursively through the JSON structure"""
    
    current_data = json_data["textbooks"][level]
    
    # Navigate to the correct folder
    if folder_path:
        folder_parts = folder_path.split("/")
        for part in folder_parts:
            current_data = current_data["folders"][part]
    
    # Process files in current level
    if "files" in current_data:
        for filename, file_info in current_data["files"].items():
            # Skip if already has archive_url (and it's not the placeholder)
            if ("archive_url" in file_info and 
                file_info["archive_url"] != "https://archive.org/......"):
                print(f"⏭️  Skipping {filename} - already has archive URL")
                continue
            
            # Skip if no original_url
            if "original_url" not in file_info:
                print(f"⏭️  Skipping {filename} - no original URL")
                continue
            
            print(f"\n📚 Processing: {filename}")
            
            # Get file info
            book_name = file_info.get("book_name", filename.replace(".pdf", ""))
            original_url = file_info["original_url"]
            
            # Extract grade from folder path
            grade = None
            stream = None
            if folder_path:
                parts = folder_path.split("/")
                if len(parts) >= 1 and parts[0].isdigit():
                    grade = parts[0]
                if len(parts) >= 2:
                    stream = parts[1]
            
            # Generate identifier
            identifier = generate_item_identifier(book_name, level, grade, stream)
            
            # Find local file first
            local_file = find_local_pdf_file(filename, level, folder_path)
            temp_file = None
            
            if local_file:
                print(f"  📁 Found local file: {local_file}")
                file_to_upload = local_file
            else:
                print(f"  🌐 Local file not found, downloading from original URL...")
                temp_file = download_pdf_if_needed(original_url, filename, level, folder_path)
                if temp_file:
                    file_to_upload = temp_file
                else:
                    print(f"  ❌ Could not get file for {filename}")
                    continue
            
            # Upload to Archive.org
            archive_url = upload_pdf_to_archive(file_to_upload, identifier, book_name, level, grade, stream)
            
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            
            if archive_url:
                # Update JSON
                success = update_json_file(json_data, level, folder_path, filename, archive_url)
                if success:
                    # Save JSON after each successful upload
                    with open(JSON_FILE, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ JSON updated for {filename}")
                else:
                    print(f"  ❌ Failed to update JSON for {filename}")
            
            # Add delay between uploads to be respectful
            print(f"  ⏸️  Waiting 3 seconds before next upload...")
            time.sleep(3)
    
    # Process subfolders
    if "folders" in current_data:
        for folder_name, folder_data in current_data["folders"].items():
            new_folder_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
            process_files_recursively(json_data, level, new_folder_path)

def main():
    """Main function to process PDFs"""
    
    # Load JSON file
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return
    
    print("🚀 STARTING NCTB TEXTBOOK UPLOAD TO ARCHIVE.ORG")
    print("✨ With proper Bengali title encoding")
    print(f"📁 Local PDF base directory: {LOCAL_PDF_BASE}")
    print(f"📂 Using collection: {COLLECTION}")
    print("=" * 80)
    
    # Ask which level to process
    levels = ["higher-secondary", "pre-primary", "primary", "secondary"]
    
    print("📖 Available education levels:")
    for i, level in enumerate(levels, 1):
        file_count = 0
        if level in json_data["textbooks"]:
            def count_files(data):
                count = 0
                if "files" in data:
                    count += len(data["files"])
                if "folders" in data:
                    for folder_data in data["folders"].values():
                        count += count_files(folder_data)
                return count
            file_count = count_files(json_data["textbooks"][level])
        
        print(f"  {i}. {level} ({file_count} files)")
    
    print(f"  0. All levels")
    
    try:
        choice = input("\nSelect level to upload (0-4): ").strip()
        
        if choice == "0":
            # Process all levels
            for level in levels:
                if level in json_data["textbooks"]:
                    print(f"\n📖 Processing {level} textbooks...")
                    print("-" * 50)
                    process_files_recursively(json_data, level)
        elif choice in ["1", "2", "3", "4"]:
            level = levels[int(choice) - 1]
            if level in json_data["textbooks"]:
                print(f"\n📖 Processing {level} textbooks...")
                print("-" * 50)
                process_files_recursively(json_data, level)
            else:
                print(f"❌ Level {level} not found in JSON")
        else:
            print("❌ Invalid choice")
            return
            
    except KeyboardInterrupt:
        print("\n⏹️  Upload interrupted by user")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "=" * 80)
    print("✅ Upload process completed!")
    print("📄 Check the JSON file for updated archive URLs")
    print("🌐 All uploaded textbooks will have proper Bengali titles")

if __name__ == "__main__":
    main()
