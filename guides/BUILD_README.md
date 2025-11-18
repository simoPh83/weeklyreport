# Quick Start - Building Executables

## Windows

```powershell
# Easy way - Use build script
.\build_windows.ps1

# Or manually
pyinstaller PropertyManagement_Windows.spec
```

Output: `dist/PropertyManagement.exe`

## macOS

```bash
# Must be run on a Mac
pyinstaller PropertyManagement_Mac.spec
```

Output: `dist/PropertyManagement.app`

## Icon Setup (Optional but Recommended)

1. Convert `graphics/ico.svg` to PNG (1024x1024)
2. Save as `graphics/icon.png`
3. Run: `python convert_icon.py`

This creates:
- `graphics/icon.ico` (Windows)
- `graphics/icon.iconset/` (Mac - convert to .icns on macOS)

## Full Documentation

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for complete details.
