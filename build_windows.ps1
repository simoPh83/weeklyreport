# Build Script for Property Management System (Windows)
# This script builds the Windows executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Property Management System - Build Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Warning: Virtual environment not activated" -ForegroundColor Yellow
    Write-Host "Activating .venv..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Check for icon
$iconPath = "graphics\icon.ico"
if (-Not (Test-Path $iconPath)) {
    Write-Host "⚠️  Warning: Icon file not found at $iconPath" -ForegroundColor Yellow
    Write-Host "The executable will be built without a custom icon." -ForegroundColor Yellow
    Write-Host "To add an icon:" -ForegroundColor Yellow
    Write-Host "  1. Convert graphics/ico.svg to PNG (1024x1024)" -ForegroundColor Yellow
    Write-Host "  2. Save as graphics/icon.png" -ForegroundColor Yellow
    Write-Host "  3. Run: python convert_icon.py" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue without icon? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Build cancelled." -ForegroundColor Red
        exit 1
    }
    # Comment out icon line in spec file
    (Get-Content PropertyManagement_Windows.spec) -replace "icon='graphics/icon.ico'", "# icon='graphics/icon.ico'  # No icon file found" | Set-Content PropertyManagement_Windows.spec
}

Write-Host "🔨 Starting build process..." -ForegroundColor Green
Write-Host ""

# Clean previous build
if (Test-Path "build") {
    Write-Host "Cleaning previous build files..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build
}
if (Test-Path "dist") {
    Write-Host "Cleaning previous distribution files..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force dist
}

# Build executable
Write-Host "Building executable with PyInstaller..." -ForegroundColor Green
& python -m PyInstaller PropertyManagement_Windows.spec

# Check if build succeeded
if ($LASTEXITCODE -eq 0 -and (Test-Path "dist\PropertyManagement.exe")) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor Cyan
    Write-Host "  dist\PropertyManagement.exe" -ForegroundColor White
    Write-Host ""
    
    $exeSize = (Get-Item "dist\PropertyManagement.exe").Length / 1MB
    Write-Host "File size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Test: dist\PropertyManagement.exe" -ForegroundColor White
    Write-Host "  2. Distribute the .exe file to users" -ForegroundColor White
    Write-Host "  3. On first run, users will select database location" -ForegroundColor White
    Write-Host ""
    
    # Ask if user wants to run the executable
    $runNow = Read-Host "Run the executable now? (y/n)"
    if ($runNow -eq "y") {
        Write-Host "Launching PropertyManagement.exe..." -ForegroundColor Green
        Start-Process "dist\PropertyManagement.exe"
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the output above for errors." -ForegroundColor Yellow
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Missing dependencies: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  - Missing UI files: Check that ui/*.ui files exist" -ForegroundColor White
    Write-Host ""
    exit 1
}
