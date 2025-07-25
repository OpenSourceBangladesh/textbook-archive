# NCTB Textbook Download Summary

## What was accomplished:

✅ **Successfully downloaded all textbook pages from the CSV file**

### Files Downloaded:
- **2025 শিক্ষাবর্ষ**: 1 file (`csv/2025/index.html`)
- **2024 শিক্ষাবর্ষ**: 2 files (`csv/2024/index.html`, `csv/2024/index_1.html`)
- **2023 শিক্ষাবর্ষ**: 2 files (`csv/2023/index.html`, `csv/2023/index_1.html`)
- **2022 শিক্ষাবর্ষ**: 1 file (`csv/2022/index.html`)
- **2021 শিক্ষাবর্ষ**: 1 file (`csv/2021/index.html`)
- **2020 শিক্ষাবর্ষ**: 1 file (`csv/2020/index.html`)
- **2019 শিক্ষাবর্ষ**: 1 file (`csv/2019/index.html`)
- **2018 শিক্ষাবর্ষ**: 1 file (`csv/2018/index.html`)
- **2017 শিক্ষাবর্ষ**: 1 file (`csv/2017/index.html`)
- **Unknown**: 1 file (`csv/unknown/index.html`) - English for Today Listening Text

### Features Implemented:

1. **Automatic Year Detection**: The script intelligently extracts years from Bengali titles
2. **Print Version Extraction**: Automatically extracts the `printable_area` content from full pages
3. **SSL Handling**: Handles both HTTP and HTTPS links with proper SSL fallback
4. **Directory Structure**: Organizes files by year in `/csv/[year]/index.html` format
5. **Duplicate Handling**: Creates numbered files when multiple content exists for same year
6. **Clean HTML Output**: Preserves original styling and table formatting

### Files Created:

1. **`download_print_pages.py`** - Main download script
2. **`requirements.txt`** - Python dependencies
3. **`csv/index.html`** - Navigation page for all downloaded content
4. **`csv/[year]/index.html`** - Individual textbook pages organized by year

### Script Features:

- **Multi-protocol support**: Tries both HTTPS and HTTP
- **SSL certificate handling**: Bypasses SSL verification issues
- **Rate limiting**: 2-second delay between requests to be respectful
- **Error handling**: Comprehensive error handling and logging
- **Bengali text support**: Properly handles Bengali numerals and text

### How to Use:

1. **Run the script**: `python download_print_pages.py`
2. **View results**: Open `csv/index.html` in a browser
3. **Navigate**: Click on any year to view that year's textbook content

### Technical Details:

- **Language**: Python 3
- **Dependencies**: requests, beautifulsoup4, lxml
- **Output Format**: Clean HTML with preserved styling
- **Character Encoding**: UTF-8 for proper Bengali text display

All pages have been successfully downloaded and are ready for offline viewing!
