# Building Executable Instructions

This guide explains how to build standalone executables for Windows and macOS.

## Prerequisites

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Prepare the Icon**:
   
   The project has `graphics/ico.svg` but executables need ICO (Windows) or ICNS (Mac) format.
   
   **Option A - Convert manually:**
   - Open `graphics/ico.svg` in any image editor (Inkscape, GIMP, Photoshop)
   - Export as PNG at 1024x1024 pixels
   - Save as `graphics/icon.png`
   - Run: `python convert_icon.py` (creates icon.ico)
   
   **Option B - Use online converter:**
   - Convert SVG to ICO: https://convertio.co/svg-ico/
   - Save as `graphics/icon.ico`
   - For Mac: https://cloudconvert.com/svg-to-icns (save as `graphics/icon.icns`)
   
   **Option C - Build without icon:**
   - The spec files will work without icons, just won't have custom icon

## Building on Windows

```bash
# Build single executable file
pyinstaller PropertyManagement_Windows.spec

# Output location
# dist/PropertyManagement.exe (single file, ~100-150 MB)
```

**What gets created:**
- `build/` - Temporary build files (can be deleted)
- `dist/PropertyManagement.exe` - **This is your distributable file!**

**To distribute:**
1. Copy `dist/PropertyManagement.exe` to target computer
2. User runs it - first launch shows database picker dialog
3. Database path is saved to `%APPDATA%\PropertyManagement\settings.pkl`

## Building on macOS

**Note:** Must be run on a Mac to create a proper .app bundle.

```bash
# Build macOS application bundle
pyinstaller PropertyManagement_Mac.spec

# Output location
# dist/PropertyManagement.app (application bundle, ~100-150 MB)
```

**What gets created:**
- `build/` - Temporary build files (can be deleted)
- `dist/PropertyManagement.app` - **This is your distributable app!**

**To distribute:**
1. Copy `dist/PropertyManagement.app` to target Mac
2. Optional: Create a DMG installer:
   ```bash
   # Install create-dmg
   brew install create-dmg
   
   # Create DMG
   create-dmg \
     --volname "Property Management" \
     --window-pos 200 120 \
     --window-size 800 400 \
     --icon-size 100 \
     --icon "PropertyManagement.app" 200 190 \
     --hide-extension "PropertyManagement.app" \
     --app-drop-link 600 185 \
     "PropertyManagement-Installer.dmg" \
     "dist/"
   ```

## Testing the Executable

### Windows:
```bash
# Run from command line to see any errors
dist\PropertyManagement.exe
```

### macOS:
```bash
# Run from Terminal
open dist/PropertyManagement.app

# Or double-click in Finder
```

## Common Issues

### 1. Missing UI Files Error
**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'ui/main_window.ui'`

**Fix:** The spec file includes UI files, but if error persists:
- Check that `ui/*.ui` files exist
- Rebuild: `pyinstaller --clean PropertyManagement_Windows.spec`

### 2. Icon Not Showing
**Fix:** 
- Ensure `graphics/icon.ico` (Windows) or `graphics/icon.icns` (Mac) exists
- If missing, build proceeds without custom icon

### 3. Large File Size
The executable is 100-150 MB because it includes:
- Python interpreter
- PyQt6 libraries
- SQLite
- All dependencies

This is normal for PyQt applications!

### 4. Antivirus False Positive (Windows)
Some antivirus may flag the .exe initially:
- This is common with PyInstaller executables
- Sign the executable with a code signing certificate to avoid this
- Or add exception in antivirus

## Advanced: Code Signing

### Windows Code Signing:
```bash
# Requires code signing certificate
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/PropertyManagement.exe
```

### macOS Code Signing:
```bash
# Requires Apple Developer account
codesign --force --deep --sign "Developer ID Application: Your Name" dist/PropertyManagement.app

# Notarize for macOS Gatekeeper
xcrun notarytool submit PropertyManagement.dmg --apple-id your@email.com --team-id TEAMID --wait
```

## File Structure After Build

```
weeklyreport/
├── build/                          # Temporary (can delete)
├── dist/
│   ├── PropertyManagement.exe      # Windows executable
│   └── PropertyManagement.app/     # macOS app bundle
├── graphics/
│   ├── ico.svg                     # Original icon
│   ├── icon.ico                    # Windows icon
│   └── icon.icns                   # Mac icon
├── PropertyManagement_Windows.spec
├── PropertyManagement_Mac.spec
└── convert_icon.py
```

## Updating the Application

When you make changes to the code:

1. **Update version number** in Mac spec file (`CFBundleShortVersionString`)
2. **Rebuild:**
   ```bash
   pyinstaller --clean PropertyManagement_Windows.spec
   ```
3. **Test the new executable**
4. **Distribute** the updated file

## Distribution Checklist

- [ ] Icon file created (icon.ico / icon.icns)
- [ ] Tested executable on clean machine
- [ ] Verified database picker appears on first run
- [ ] Verified application remembers database path
- [ ] Tested "Change Database Path" menu option
- [ ] Checked file size is reasonable (< 200 MB)
- [ ] (Optional) Code signed for production
- [ ] (Optional) Created installer (Inno Setup for Windows, DMG for Mac)

## Need Help?

- PyInstaller docs: https://pyinstaller.org/
- Icon conversion: https://convertio.co/
- Code signing: https://developer.apple.com/support/code-signing/
