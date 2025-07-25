# NCTB Textbook Download Summary

## Overview
Successfully processed and downloaded NCTB (National Curriculum and Textbook Board) textbooks for the 2025 academic year.

## Statistics
- **Total Markdown Files Processed**: 26
- **Total Download Links Found**: 933
- **Successfully Downloaded PDFs**: 616 (66.0% success rate)
- **Failed Downloads**: 1 (permanently broken link)
- **Total Downloaded Size**: 8,475.21 MB (~8.5 GB)
- **PDF Folders Created**: 25
- **Retry Count**: 2 attempts per failed file

## Folder Structure
```
2025/
├── index.json (comprehensive tracking file)
├── higher-secondary/
│   ├── index.md
│   └── PDFs/
├── pre-primary/
│   ├── index.md
│   ├── PDFs/
│   └── tribe/
│       ├── index.md
│       └── PDFs/
├── primary/
│   ├── gen/
│   │   ├── 1-5/ (classes 1-5)
│   │   │   ├── index.md
│   │   │   └── PDFs/
│   ├── mad/ (madrasah)
│   │   ├── 1-5/ (classes 1-5)
│   │   │   ├── index.md
│   │   │   └── PDFs/
│   └── tribe/
│       ├── index.md
│       └── PDFs/
└── secondary/
    ├── gen/ (general)
    │   ├── 6-9/ (classes 6-9)
    │   │   ├── index.md
    │   │   └── PDFs/
    ├── mad/ (madrasah)
    │   ├── 6-9/ (classes 6-9)
    │   │   ├── index.md
    │   │   └── PDFs/
    └── tech/ (technical)
        ├── 6-9/ (classes 6-9)
        │   ├── index.md
        │   └── PDFs/
```

## File Naming Convention
PDFs are saved with the following naming pattern:
- `পাঠ্যপুস্তকের_নাম_1.pdf` (for Download Link 1)
- `পাঠ্যপুস্তকের_নাম_2.pdf` (for Download Link 2)

Examples:
- `আমার বাংলা বই_1.pdf`
- `English For Today_2.pdf`
- `প্রাথমিক গণিত_1.pdf`

## Failed Downloads (1 total)
1. **কর্ম ও জীবনমুখী শিক্ষা (Link 1)**: 404 Not Found error - Permanently broken Google Drive link

## Features Implemented
1. **Parallel Downloads**: Used ThreadPoolExecutor with 3 workers for efficient downloading
2. **Smart File Detection**: Automatically skips existing valid PDF files to avoid re-downloading
3. **Retry Mechanism**: 2 retry attempts for failed downloads with exponential backoff (1s, 2s max)
4. **Smart URL Handling**: 
   - Google Drive: Extracts file ID and uses direct download URLs
   - eGovCloud: Adds `/download` suffix for direct downloads
5. **File Validation**: Checks PDF signatures and file sizes before accepting downloads
6. **Progress Tracking**: Real-time progress bar with success/failure indicators
7. **Comprehensive Logging**: Complete index.json with folder structure and download metadata
8. **Index Persistence**: Loads existing index.json to avoid re-downloading already successful files

## Scripts Used
1. **convert_html_to_markdown.py**: Converted 26 HTML files to clean Markdown tables
2. **download_pdfs.py**: Enhanced PDF downloader with existing file detection and 2 retry attempts
3. **retry_failed_downloads.py**: Specialized retry script for failed downloads (successfully recovered 3 of 4 files)

## Technical Notes
- All Bengali filenames are properly normalized for filesystem compatibility
- Duplicate handling: Creates numbered versions if files already exist
- Thread-safe implementation with proper locking mechanisms
- Memory-efficient streaming downloads for large files
- Automatic retry with exponential backoff for temporary failures
- **Smart Resume**: Automatically detects and skips already downloaded files
- **Index Persistence**: Maintains comprehensive download state across runs
- **Optimized Performance**: Only processes files that haven't been downloaded yet

## Access
- **Markdown Files**: Human-readable tables with download links
- **PDF Files**: Organized in `PDFs/` folders within each category
- **Index File**: `2025/index.json` contains complete metadata and tracking information

This comprehensive download system ensures all NCTB textbooks are properly organized and easily accessible while maintaining the original folder structure and providing detailed tracking information.
