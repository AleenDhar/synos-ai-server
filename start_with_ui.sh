#!/bin/bash

# Start DeepAgent Server with Gradio UI
# This script starts both the FastAPI server and Gradio UI

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        Starting DeepAgent with Google Sheets UI             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if client_secrets.json exists
if [ ! -f "client_secrets.json" ]; then
    echo "⚠️  Warning: client_secrets.json not found!"
    echo "   Google Sheets integration will not work until you:"
    echo "   1. Download OAuth credentials from Google Cloud Console"
    echo "   2. Save as client_secrets.json in project root"
    echo ""
    echo "   See GOOGLE_SHEETS_SETUP.md for detailed instructions"
    echo ""
fi

# Start FastAPI server in background
echo "🚀 Starting FastAPI server on http://localhost:8000..."
python server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Start Gradio UI
echo "🎨 Starting Gradio UI on http://localhost:7860..."
python gradio_ui.py &
UI_PID=$!

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Both servers are running!                                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  FastAPI Server: http://localhost:8000                      ║"
echo "║  Gradio UI:      http://localhost:7860                      ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Press Ctrl+C to stop both servers                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping servers...'; kill $SERVER_PID $UI_PID; exit" INT
wait
