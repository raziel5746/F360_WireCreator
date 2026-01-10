# ==============================================================================
# Deploy Simple Wire Creator to Fusion 360
# ==============================================================================
# 
# HOW TO RUN THIS SCRIPT:
# 1. Open PowerShell
# 2. Navigate to this folder: cd "c:\Users\razie\Desktop\My Fusion Add-ins\WireCreator"
# 3. Run: .\deploy.ps1
#
# If you get an execution policy error, run PowerShell as Admin and execute:
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# ==============================================================================

$SourceDir = $PSScriptRoot
$FusionAddInsDir = "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\SimpleWireCreator"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Deploying Simple Wire Creator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if target directory exists
if (-not (Test-Path $FusionAddInsDir)) {
    Write-Host "Creating add-in directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $FusionAddInsDir -Force | Out-Null
}

# Copy main files
Write-Host "[1/3] Copying SimpleWireCreator.py..." -ForegroundColor Green
Copy-Item -Path "$SourceDir\SimpleWireCreator.py" -Destination $FusionAddInsDir -Force

Write-Host "[2/3] Copying SimpleWireCreator.manifest..." -ForegroundColor Green
Copy-Item -Path "$SourceDir\SimpleWireCreator.manifest" -Destination $FusionAddInsDir -Force

# Copy Resources folder
if (Test-Path "$SourceDir\Resources") {
    Write-Host "[3/3] Copying Resources folder..." -ForegroundColor Green
    Copy-Item -Path "$SourceDir\Resources" -Destination $FusionAddInsDir -Recurse -Force
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: $FusionAddInsDir" -ForegroundColor Gray
Write-Host ""
Write-Host "NEXT STEP: Restart Fusion 360 or stop/start the add-in." -ForegroundColor Yellow
Write-Host ""
