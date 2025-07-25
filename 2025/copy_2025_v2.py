#!/usr/bin/env python3
"""
Script to copy 2025 folder to 2025V2 keeping only PDFs ending with _2.pdf
Maintains folder structure but filters out _1.pdf files
"""

import os
import shutil
from pathlib import Path
import json
import time

class FolderCopyFilter:
    def __init__(self, source_dir="2025", target_dir="2025V2"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.copied_files = []
        self.skipped_files = []
        self.copied_folders = []
        self.total_size = 0

    def copy_with_filter(self):
        """Copy folder structure and filter PDFs"""
        print("📁 PDF Filter Copy Tool")
        print("=" * 60)
        print(f"📂 Source: {self.source_dir}")
        print(f"📂 Target: {self.target_dir}")
        print("🎯 Filter: Keep only PDFs ending with '_2.pdf'")
        print("=" * 60)

        # Check if source directory exists
        if not self.source_dir.exists():
            print(f"❌ Source directory '{self.source_dir}' does not exist!")
            return False

        # Check if target directory already exists
        if self.target_dir.exists():
            response = input(f"⚠️  Target directory '{self.target_dir}' already exists. Delete it? (y/N): ")
            if response.lower() == 'y':
                print(f"🗑️  Removing existing '{self.target_dir}'...")
                shutil.rmtree(self.target_dir)
            else:
                print("❌ Operation cancelled.")
                return False

        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created target directory: {self.target_dir}")

        # Walk through source directory
        for root, dirs, files in os.walk(self.source_dir):
            root_path = Path(root)
            relative_path = root_path.relative_to(self.source_dir)
            target_root = self.target_dir / relative_path

            # Create directory structure
            target_root.mkdir(parents=True, exist_ok=True)
            
            if relative_path != Path('.'):  # Don't count root directory
                self.copied_folders.append(str(relative_path))
                print(f"📁 Created: {relative_path}")

            # Process files in current directory
            for file in files:
                source_file = root_path / file
                target_file = target_root / file
                
                # Filter logic
                if file.endswith('.pdf'):
                    if file.endswith('_2.pdf'):
                        # Copy _2.pdf files
                        try:
                            shutil.copy2(source_file, target_file)
                            file_size = source_file.stat().st_size
                            self.total_size += file_size
                            self.copied_files.append({
                                'source': str(source_file),
                                'target': str(target_file),
                                'relative_path': str(relative_path / file),
                                'size': file_size
                            })
                            print(f"  ✅ Copied: {relative_path / file} ({file_size / (1024*1024):.1f} MB)")
                        except Exception as e:
                            print(f"  ❌ Error copying {file}: {e}")
                    else:
                        # Skip _1.pdf and other PDF files
                        self.skipped_files.append({
                            'file': str(relative_path / file),
                            'reason': 'Not _2.pdf'
                        })
                        print(f"  ⏭️  Skipped: {relative_path / file} (not _2.pdf)")
                else:
                    # Copy non-PDF files (markdown, json, etc.)
                    try:
                        shutil.copy2(source_file, target_file)
                        file_size = source_file.stat().st_size
                        self.copied_files.append({
                            'source': str(source_file),
                            'target': str(target_file),
                            'relative_path': str(relative_path / file),
                            'size': file_size
                        })
                        print(f"  📄 Copied: {relative_path / file}")
                    except Exception as e:
                        print(f"  ❌ Error copying {file}: {e}")

        return True

    def generate_report(self):
        """Generate a detailed report of the copy operation"""
        report_data = {
            "operation": "PDF Filter Copy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_directory": str(self.source_dir),
            "target_directory": str(self.target_dir),
            "filter_criteria": "Keep only PDFs ending with '_2.pdf'",
            "statistics": {
                "total_files_copied": len(self.copied_files),
                "total_files_skipped": len(self.skipped_files),
                "total_folders_created": len(self.copied_folders),
                "total_size_bytes": self.total_size,
                "total_size_mb": round(self.total_size / (1024*1024), 2)
            },
            "copied_files": self.copied_files,
            "skipped_files": self.skipped_files,
            "folders_created": self.copied_folders
        }

        # Save report
        report_path = self.target_dir / "copy_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return report_data

    def print_summary(self, report_data):
        """Print operation summary"""
        print(f"\n{'='*60}")
        print("📊 COPY OPERATION SUMMARY")
        print(f"{'='*60}")
        
        stats = report_data['statistics']
        print(f"📁 Folders created: {stats['total_folders_created']}")
        print(f"📄 Files copied: {stats['total_files_copied']}")
        print(f"⏭️  Files skipped: {stats['total_files_skipped']}")
        print(f"💾 Total size: {stats['total_size_mb']} MB")

        # Count PDF files specifically
        pdf_copied = len([f for f in self.copied_files if f['relative_path'].endswith('.pdf')])
        pdf_skipped = len([f for f in self.skipped_files if f['file'].endswith('.pdf')])
        
        print(f"\n📊 PDF Statistics:")
        print(f"   ✅ PDF files copied (_2.pdf): {pdf_copied}")
        print(f"   ⏭️  PDF files skipped (_1.pdf and others): {pdf_skipped}")

        # Show some examples
        if pdf_copied > 0:
            print(f"\n📖 Sample copied PDFs:")
            for i, file_info in enumerate([f for f in self.copied_files if f['relative_path'].endswith('.pdf')][:5]):
                print(f"   {i+1}. {file_info['relative_path']}")
            if pdf_copied > 5:
                print(f"   ... and {pdf_copied - 5} more")

        print(f"\n📋 Report saved: {self.target_dir / 'copy_report.json'}")
        print(f"🎉 Copy operation completed successfully!")

    def run(self):
        """Main execution method"""
        success = self.copy_with_filter()
        
        if success:
            report_data = self.generate_report()
            self.print_summary(report_data)
            return True
        else:
            return False

def main():
    """Main function"""
    copier = FolderCopyFilter(source_dir="2025", target_dir="2025V2")
    copier.run()

if __name__ == "__main__":
    main()
