#!/bin/bash

# DeepAgent Server Startup Script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                DeepAgent Server Launcher                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/installed" ]; then
    echo ""
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    
    touch venv/installed
    echo "✓ Dependencies installed"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "📝 Please edit .env file and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (required)"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit and edit .env..."
fi

# Load environment variables
source .env 2>/dev/null

# Check for ANTHROPIC_API_KEY only if using Anthropic model
if [[ "$MODEL" =~ ^anthropic ]]; then
    if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
        echo ""
        echo "❌ ANTHROPIC_API_KEY not set in .env file"
        echo "   Please add your Anthropic API key to the .env file"
        echo ""
        echo "   Get your API key from: https://console.anthropic.com/"
        echo ""
        echo "   Or use Gemini (free tier!) or Ollama instead:"
        echo "   MODEL=google_genai:gemini-2.0-flash-exp"
        echo "   GOOGLE_API_KEY=your_key"
        exit 1
    fi
fi

# Check for model-specific API keys
if [[ "$MODEL" =~ ^google_genai ]]; then
    if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
        echo ""
        echo "❌ GOOGLE_API_KEY not set for Gemini model"
        echo "   Please add your Google API key to the .env file"
        echo ""
        echo "   Get FREE API key from: https://aistudio.google.com/"
        echo "   Free tier: 1,500 requests/day!"
        exit 1
    fi
    echo "✓ Using Gemini model: $MODEL"
elif [[ "$MODEL" =~ ^openai ]]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo ""
        echo "❌ OPENAI_API_KEY not set for OpenAI model"
        echo "   Please add your OpenAI API key to the .env file"
        exit 1
    fi
    echo "✓ Using OpenAI model: $MODEL"
elif [[ "$MODEL" =~ ^ollama ]]; then
    echo "✓ Using local Ollama model: $MODEL"
    echo "   Make sure Ollama is running: ollama serve"
else
    echo "✓ Using Anthropic model: $MODEL"
fi

# Create required directories
echo ""
echo "📁 Checking directories..."
mkdir -p custom_tools
mkdir -p workspace
echo "✓ Directories ready"

# Check for Google Sheets credentials
if [ ! -f "client_secrets.json" ]; then
    echo ""
    echo "⚠️  Warning: client_secrets.json not found!"
    echo "   Google Sheets integration will not work until you:"
    echo "   1. Download OAuth credentials from Google Cloud Console"
    echo "   2. Save as client_secrets.json in project root"
    echo ""
    echo "   See GOOGLE_SHEETS_SETUP.md for detailed instructions"
    echo ""
fi

# Start servers
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Starting DeepAgent with Gradio UI                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $SERVER_PID $UI_PID 2>/dev/null
    deactivate
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Start FastAPI server in background
echo "🚀 Starting FastAPI server on http://localhost:8000..."
python server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Failed to start FastAPI server"
    exit 1
fi

# Start Gradio UI in background
echo "🎨 Starting Gradio UI on http://localhost:7860..."
python gradio_ui.py &
UI_PID=$!

# Wait for UI to start
sleep 2

# Check if UI started successfully
if ! kill -0 $UI_PID 2>/dev/null; then
    echo "❌ Failed to start Gradio UI"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Both servers are running!                                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  FastAPI Server: http://localhost:8000                      ║"
echo "║  Gradio UI:      http://localhost:7860                      ║"
echo "║                                                              ║"
echo "║  Open Gradio UI in your browser to get started!             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Press Ctrl+C to stop both servers                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Wait for both processes
wait