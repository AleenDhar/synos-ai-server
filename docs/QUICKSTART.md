# 🚀 Quick Start Guide

Get your DeepAgent server running in 5 minutes!

## Prerequisites

- Python 3.11+
- Anthropic API key ([Get one](https://console.anthropic.com/))

## Installation

### Option A: Startup Script (Recommended)

```bash
chmod +x start.sh
./start.sh
```

### Option B: Manual

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Start
python server.py
```

## Configuration

Edit `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Optional:
```bash
PORT=8080
MODEL=openai:gpt-4o
OPENAI_API_KEY=sk-your-key
```

## Access

Open http://localhost:8000

## Try It Out

### Simple Search
```
"What are the latest developments in quantum computing?"
```

### Deep Research
```
"Write a comprehensive report on renewable energy trends"
```

### Custom Tools
```
"Calculate 15% of 250"
```

## Next Steps

### Add Custom Tools

Create `custom_tools/my_tools.py`:
```python
from langchain_core.tools import tool

@tool
def my_tool(text: str) -> str:
    """Description."""
    return f"Processed: {text}"
```

### Add MCP Servers

1. Click **MCP** tab
2. Click **Add MCP Server**
3. Configure and enable

### Customize Instructions

1. Click **Config** tab
2. Enter custom instructions
3. Click **Update**

## Troubleshooting

**Module not found:**
```bash
pip install --upgrade -r requirements.txt
```

**Connection refused:**
```bash
lsof -i :8000
PORT=8080 python server.py
```

**API key not found:**
Ensure `.env` contains `ANTHROPIC_API_KEY=sk-ant-...`

## Learn More

- [API Reference](API.md)
- [Google Sheets Integration](GOOGLE_SHEETS.md)
- [Deployment Guide](DEPLOYMENT.md)
