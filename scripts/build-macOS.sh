#!/bin/bash

set -e

echo "🔍 Checking system requirements for PyInstaller build..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 is not installed. Install it with:"
  echo "    brew install python"
  exit 1
fi

# Check current directory
if [ ! -f "apis/main.py" ]; then
  echo "❌ Please run this script from the golem directory (where apis/main.py exists)"
  exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "⚙️ Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate and install dependencies
echo "📦 Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create the standalone script
echo "📝 Creating standalone main script..."
cat > main_standalone.py << 'EOF'
#!/usr/bin/env python3
"""
Standalone FastAPI Golem Provider API
Bundled with PyInstaller for single executable deployment
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
if getattr(sys, 'frozen', False):
    # If running as PyInstaller bundle
    bundle_dir = Path(sys.executable).parent
    sys.path.insert(0, str(bundle_dir))
else:
    # If running as script
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

# Now import the FastAPI app
try:
    from apis.main import app
    import uvicorn
    
    def main():
        print("🚀 Starting Golem Provider API Server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API documentation: http://localhost:8000/docs")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure all dependencies are installed and paths are correct.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
EOF

# Create PyInstaller spec file for better control
echo "📝 Creating PyInstaller spec file..."
cat > golem_api.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('apis/*.py', 'apis'),
    ],
    hiddenimports=[
        'uvicorn.workers',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'fastapi',
        'pydantic',
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
    name='golem-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

echo "🔨 Building standalone executable with PyInstaller..."
pyinstaller golem_api.spec --clean --noconfirm

# Check if build was successful
if [ -f "dist/golem-api" ]; then
    echo "✅ Build successful!"
    echo ""
    echo "📦 Executable created: dist/golem-api"
    echo "📏 File size: $(du -h dist/golem-api | cut -f1)"
    echo ""
    echo "🚀 To run the standalone executable:"
    echo "    ./dist/golem-api"
    echo ""
    echo "📋 To distribute:"
    echo "    1. Copy 'dist/golem-api' to target machine"
    echo "    2. Make executable: chmod +x golem-api"
    echo "    3. Run: ./golem-api"
    echo ""
    echo "ℹ️  Note: The target machine needs:"
    echo "   - golemsp installed (for Golem operations)"
    echo "   - Appropriate system permissions for VM/KVM operations"
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi
