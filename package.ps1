# ==============================================================================
# Create App Store Submission Package
# ==============================================================================
# 
# HOW TO RUN THIS SCRIPT:
# 1. Open PowerShell
# 2. Navigate to this folder: cd "c:\Users\razie\Desktop\My Fusion Add-ins\WireCreator"
# 3. Run: .\package.ps1
#
# This script creates SimpleWireCreator.zip for Autodesk App Store submission.
#
# ==============================================================================

$SourceDir = $PSScriptRoot
$BundleName = "SimpleWireCreator.bundle"
$ZipName = "SimpleWireCreator.zip"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Creating App Store Package" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# First, sync the bundle with latest source files
Write-Host "[1/3] Syncing bundle with source files..." -ForegroundColor Green
Copy-Item -Path "$SourceDir\SimpleWireCreator.py" -Destination "$SourceDir\$BundleName\Contents\" -Force
Copy-Item -Path "$SourceDir\SimpleWireCreator.manifest" -Destination "$SourceDir\$BundleName\Contents\" -Force

# Sync Resources folder
if (Test-Path "$SourceDir\Resources") {
    Copy-Item -Path "$SourceDir\Resources" -Destination "$SourceDir\$BundleName\Contents\" -Recurse -Force
}

# Remove old zip if exists
if (Test-Path "$SourceDir\$ZipName") {
    Write-Host "[2/3] Removing old zip file..." -ForegroundColor Yellow
    Remove-Item "$SourceDir\$ZipName" -Force
}

# Create new zip
Write-Host "[3/3] Creating $ZipName..." -ForegroundColor Green
Compress-Archive -Path "$SourceDir\$BundleName" -DestinationPath "$SourceDir\$ZipName"

$zipSize = (Get-Item "$SourceDir\$ZipName").Length / 1KB
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Package Created!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output: $SourceDir\$ZipName" -ForegroundColor Gray
Write-Host "Size: $([math]::Round($zipSize, 2)) KB" -ForegroundColor Gray
Write-Host ""
Write-Host "NEXT STEP: Upload $ZipName to Autodesk App Store." -ForegroundColor Yellow
Write-Host ""
