# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Property Management System (macOS)

To build the .app bundle:
    pyinstaller PropertyManagement_Mac.spec

The .app will be in the 'dist' folder.

Note: Must be built on macOS to create a proper .app bundle.
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui/*.ui', 'ui'),  # Include all UI files
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'qdarktheme',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PropertyManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='PropertyManagement.app',
    icon='graphics/icon.icns',  # macOS icon
    bundle_identifier='com.yourcompany.propertymanagement',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleName': 'Property Management',
        'CFBundleDisplayName': 'Property Management System',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025',
        'NSHighResolutionCapable': 'True',
    },
)
