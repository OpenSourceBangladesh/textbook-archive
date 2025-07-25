# PowerShell script to count PDF files with _1.pdf and _2.pdf suffixes
# Usage: .\count_pdfs.ps1

param(
    [string]$BasePath = "2025"
)

Write-Host "📊 PDF Suffix Counter (PowerShell)" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

# Check if directory exists
if (-not (Test-Path $BasePath)) {
    Write-Host "❌ Directory $BasePath does not exist!" -ForegroundColor Red
    exit 1
}

$FullPath = Resolve-Path $BasePath
Write-Host "🔍 Scanning $FullPath for PDF files..." -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Gray

# Get all PDF files recursively
$AllPDFs = Get-ChildItem -Path $BasePath -Recurse -Filter "*.pdf" -File

$TotalPDFs = $AllPDFs.Count
Write-Host "📁 Total PDF files found: $TotalPDFs" -ForegroundColor Green
Write-Host

# Initialize counters
$Count_1 = 0
$Count_2 = 0
$CountOther = 0

# Count by suffix
foreach ($pdf in $AllPDFs) {
    if ($pdf.Name -match "_1\.pdf$") {
        $Count_1++
    }
    elseif ($pdf.Name -match "_2\.pdf$") {
        $Count_2++
    }
    else {
        $CountOther++
    }
}

# Print summary
Write-Host "📊 Summary by Suffix:" -ForegroundColor Cyan
Write-Host ("-" * 30) -ForegroundColor Gray

$Percentage_1 = if ($TotalPDFs -gt 0) { ($Count_1 / $TotalPDFs * 100) } else { 0 }
$Percentage_2 = if ($TotalPDFs -gt 0) { ($Count_2 / $TotalPDFs * 100) } else { 0 }
$PercentageOther = if ($TotalPDFs -gt 0) { ($CountOther / $TotalPDFs * 100) } else { 0 }

Write-Host ("  _1.pdf    : {0,4} files ({1,5:F1}%)" -f $Count_1, $Percentage_1) -ForegroundColor White
Write-Host ("  _2.pdf    : {0,4} files ({1,5:F1}%)" -f $Count_2, $Percentage_2) -ForegroundColor White
Write-Host ("  other     : {0,4} files ({1,5:F1}%)" -f $CountOther, $PercentageOther) -ForegroundColor White

Write-Host

# Breakdown by folder
Write-Host "📂 Breakdown by Folder:" -ForegroundColor Cyan
Write-Host ("-" * 50) -ForegroundColor Gray

# Group by directory
$GroupedByFolder = $AllPDFs | Group-Object { $_.Directory.FullName }

foreach ($group in ($GroupedByFolder | Sort-Object Name)) {
    $FolderPath = $group.Name -replace [regex]::Escape($FullPath), ""
    if ($FolderPath.StartsWith("\")) {
        $FolderPath = $FolderPath.Substring(1)
    }
    
    $FolderFiles = $group.Group
    $TotalInFolder = $FolderFiles.Count
    
    $Folder_1 = ($FolderFiles | Where-Object { $_.Name -match "_1\.pdf$" }).Count
    $Folder_2 = ($FolderFiles | Where-Object { $_.Name -match "_2\.pdf$" }).Count
    $FolderOther = ($FolderFiles | Where-Object { $_.Name -notmatch "_[12]\.pdf$" }).Count
    
    Write-Host "`n📁 ${FolderPath}:" -ForegroundColor Yellow
    Write-Host "   Total: $TotalInFolder files" -ForegroundColor White
    
    if ($Folder_1 -gt 0) {
        Write-Host "   _1.pdf: $Folder_1 files" -ForegroundColor Green
    }
    if ($Folder_2 -gt 0) {
        Write-Host "   _2.pdf: $Folder_2 files" -ForegroundColor Green
    }
    if ($FolderOther -gt 0) {
        Write-Host "   other:  $FolderOther files" -ForegroundColor Magenta
    }
}

# Analysis
Write-Host "`n🔍 Analysis:" -ForegroundColor Cyan
Write-Host ("-" * 20) -ForegroundColor Gray

if ($Count_1 -eq $Count_2) {
    Write-Host "✅ Equal number of _1.pdf and _2.pdf files - Good!" -ForegroundColor Green
}
else {
    $Diff = [Math]::Abs($Count_1 - $Count_2)
    if ($Count_1 -gt $Count_2) {
        Write-Host "⚠️  More _1.pdf files than _2.pdf files (difference: $Diff)" -ForegroundColor Yellow
    }
    else {
        Write-Host "⚠️  More _2.pdf files than _1.pdf files (difference: $Diff)" -ForegroundColor Yellow
    }
}

if ($CountOther -gt 0) {
    Write-Host "⚠️  Found $CountOther files with non-standard naming" -ForegroundColor Yellow
}
else {
    Write-Host "✅ All PDF files follow the standard naming convention" -ForegroundColor Green
}

# Expected vs actual
$ExpectedTotal = 933
if ($TotalPDFs -eq $ExpectedTotal) {
    Write-Host "✅ Total PDF count matches expected ($ExpectedTotal)" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Total PDF count ($TotalPDFs) differs from expected ($ExpectedTotal)" -ForegroundColor Yellow
}

# Final summary
Write-Host "`n🎯 Final Summary:" -ForegroundColor Cyan
Write-Host "   Total PDFs: $TotalPDFs" -ForegroundColor White
Write-Host "   _1.pdf files: $Count_1" -ForegroundColor White
Write-Host "   _2.pdf files: $Count_2" -ForegroundColor White
Write-Host "   Other files: $CountOther" -ForegroundColor White
