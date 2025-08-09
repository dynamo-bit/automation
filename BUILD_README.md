# Building Golem API as Standalone Executable

This guide shows how to create a single standalone executable of the Golem Provider API using PyInstaller, similar to how `pkg` works for Node.js applications.

## Quick Start

1. **Build the executable:**
   ```bash
   cd golem
   ./scripts/build-macOS.sh
   ```

2. **Run the standalone executable:**
   ```bash
   ./dist/golem-api
   ```

## What Gets Built

- **Input**: FastAPI application with multiple modules (`apis/main.py`, `apis/bootstrap_host.py`)
- **Output**: Single executable file `dist/golem-api` (~50-80MB)
- **Dependencies**: All Python dependencies bundled inside the executable

## Distribution

To distribute your application:

1. Copy `dist/golem-api` to the target machine
2. Make it executable: `chmod +x golem-api`
3. Run: `./golem-api`

**Requirements on target machine:**
- No Python installation needed ✅
- No pip/virtual environment needed ✅
- `golemsp` must be installed (for Golem operations)
- Appropriate system permissions for VM/KVM operations

## API Endpoints

Once running, the API will be available at `http://localhost:8000`:

- **Documentation**: `http://localhost:8000/docs`
- **Bootstrap**: `POST /bootstrap`
- **Golem Status**: `GET /golem-status`
- **Start Golem**: `POST /start-golem`
- **Stop Golem**: `POST /stop-golem`
- And more...

## Build Process Details

The build script:
1. Creates a Python virtual environment
2. Installs dependencies (FastAPI, uvicorn, PyInstaller)
3. Creates a standalone entry point script
4. Uses PyInstaller with custom spec file
5. Bundles everything into a single executable

## Troubleshooting

- **Import errors**: Make sure all Python files are in the correct directory structure
- **Build fails**: Check that Python 3 is installed and accessible
- **Runtime errors**: Ensure `golemsp` is installed on the target system
