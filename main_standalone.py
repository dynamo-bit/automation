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
