#!/bin/bash

set -e

echo "🔍 Checking system requirements for macOS..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
  echo " Python 3 is not installed. Install it with:"
  echo "    brew install python"
  exit 1
fi

# Check for Multipass
if ! command -v multipass &> /dev/null; then
  echo " Multipass is not installed. Install it from:"
  echo "    https://multipass.run/"
  exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "⚙️ Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate and install dependencies
source .venv/bin/activate
echo "📦 Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic requests

# Start API
echo "🚀 Starting FastAPI server at http://localhost:8000"
uvicorn apis.main:app --host 0.0.0.0 --port 8000
