"""
Convert SVG icon to ICO (Windows) and PNG for ICNS (Mac)
Note: SVG needs to be converted to PNG first manually or use an online converter
"""
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError as e:
    print(f"Error: {e}")
    print("Install dependencies: pip install pillow")
    sys.exit(1)

# Paths
svg_path = Path("graphics/ico.svg")
ico_path = Path("graphics/icon.ico")
icns_path = Path("graphics/icon.icns")

print("""
SVG Icon Conversion Instructions:
==================================

Since SVG conversion requires native libraries, please follow these steps:

1. Convert SVG to PNG (1024x1024) using one of these methods:
   - Open in Inkscape/GIMP and export as PNG
   - Use online converter: https://svgtopng.com/
   - Use ImageMagick: magick convert -density 300 ico.svg -resize 1024x1024 icon.png

2. Save the PNG as: graphics/icon.png

3. Run this script again to create ICO and ICNS files

Alternatively, I can create the PyInstaller spec files now, and you can
add the icon manually later.
""")

# Check if PNG already exists
png_path = Path("graphics/icon.png")
if not png_path.exists():
    print(f"✗ {png_path} not found. Please convert SVG to PNG first.")
    print("\nCreating spec files without icon for now...")
    sys.exit(0)

print(f"✓ Found {png_path}")
print(f"\nConverting to ICO and ICNS formats...")

# Load PNG
img = Image.open(png_path)

# Create ICO (Windows) with multiple sizes
print("  -> Creating ICO (Windows)...")
ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(ico_path, format='ICO', sizes=ico_sizes)
print(f"  ✓ Created: {ico_path}")

# Create iconset folder for ICNS (Mac)
print("  -> Creating iconset for ICNS (Mac)...")
iconset_path = Path("graphics/icon.iconset")
iconset_path.mkdir(exist_ok=True)

# macOS iconset requires specific sizes
icns_sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

for size, filename in icns_sizes:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(iconset_path / filename)

print(f"  ✓ Created iconset: {iconset_path}")

# Instructions for creating ICNS
print(f"\n✓ Icon conversion complete!")
print(f"\nCreated files:")
print(f"  - Windows: {ico_path}")
print(f"  - Mac iconset: {iconset_path}")
print(f"\nTo create .icns on macOS, run:")
print(f"  iconutil -c icns {iconset_path}")
print(f"\nOr use online converter: https://cloudconvert.com/iconset-to-icns")

