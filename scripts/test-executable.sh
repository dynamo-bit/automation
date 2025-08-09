#!/bin/bash

set -e

echo "🧪 Testing the standalone executable..."

# Check if executable exists
if [ ! -f "dist/golem-api" ]; then
    echo "❌ Executable not found. Run ./scripts/build-macOS.sh first."
    exit 1
fi

echo "✅ Executable found: dist/golem-api"
echo "📏 File size: $(du -h dist/golem-api | cut -f1)"

# Test that it's executable
if [ ! -x "dist/golem-api" ]; then
    echo "⚙️ Making executable..."
    chmod +x dist/golem-api
fi

echo "🚀 Starting executable for 10 seconds to test..."
echo "   (Server will run in background, then be stopped)"

# Start the executable in background
./dist/golem-api &
API_PID=$!

# Wait a moment for startup
sleep 5

# Test if it's responding
echo "🔍 Testing API response..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ API is responding!"
    
    # Try to get the status endpoint
    echo "🔍 Testing status endpoint..."
    if curl -s http://localhost:8000/golem-status > /dev/null; then
        echo "✅ Status endpoint accessible!"
    else
        echo "⚠️ Status endpoint may require golemsp installation"
    fi
else
    echo "❌ API not responding on localhost:8000"
fi

# Stop the process
echo "🛑 Stopping test server..."
kill $API_PID 2>/dev/null || true
sleep 2

echo ""
echo "🎉 Test completed!"
echo "💡 To run manually: ./dist/golem-api"
