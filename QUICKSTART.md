# 🚀 Quick Start Guide

Get your DeepAgent server running in 5 minutes!

## Step 1: Prerequisites

Make sure you have:
- ✅ Python 3.11 or higher
- ✅ An Anthropic API key ([Get one here](https://console.anthropic.com/))

Optional:
- Node.js (for MCP servers)
- Docker (for containerized deployment)

## Step 2: Install

### Option A: Using the Startup Script (Recommended)

```bash
# Make the script executable (if not already)
chmod +x start.sh

# Run the startup script
./start.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Check for configuration
- Start the server

### Option B: Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your API key
nano .env  # Or use any text editor

# Start the server
python server.py
```

### Option C: Using Docker

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your API key
nano .env

# Start with Docker Compose
docker-compose up -d
```

## Step 3: Configure

Open the `.env` file and add your API key:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

That's the only required configuration!

Optional settings:
```bash
# Use a different port
PORT=8080

# Use OpenAI instead
MODEL=openai:gpt-4o
OPENAI_API_KEY=sk-your-openai-key

# Use local Ollama
MODEL=ollama:llama3.1
```

## Step 4: Access

Once the server starts, you'll see:

```
╔══════════════════════════════════════════════════════════════╗
║                    DeepAgent Server v1.0                     ║
╠══════════════════════════════════════════════════════════════╣
║  Features:                                                   ║
║  ✓ Free web search with DuckDuckGo                          ║
║  ✓ Deep research with specialized agents                    ║
║  ✓ MCP server support (dynamic tools)                       ║
║  ✓ Custom tools integration                                 ║
║  ✓ Streaming responses                                      ║
║  ✓ Web UI for easy interaction                             ║
╠══════════════════════════════════════════════════════════════╣
║  Starting on: http://0.0.0.0:8000                           ║
╚══════════════════════════════════════════════════════════════╝
```

Open your browser and go to: **http://localhost:8000**

## Step 5: Try It Out

### Example 1: Simple Search

```
You: What are the latest developments in quantum computing?

Agent: I'll search for recent information...
[Searches web using DuckDuckGo]
[Returns formatted results with sources]
```

### Example 2: Deep Research

```
You: Write a comprehensive report on renewable energy trends in 2025

Agent: I'll conduct deep research on this topic...
[Creates research plan]
[Delegates to research agents]
[Synthesizes findings]
[Provides detailed report]
```

### Example 3: Using Custom Tools

```
You: Calculate 15% of 250

Agent: [Uses calculator tool]
The result is 37.5
```

## 🎯 Next Steps

### Add Custom Tools

1. Create a new file in `custom_tools/`:
   ```bash
   nano custom_tools/my_tools.py
   ```

2. Add your tool:
   ```python
   from langchain_core.tools import tool
   
   @tool
   def my_tool(text: str) -> str:
       """Description of what this does."""
       return f"Processed: {text}"
   ```

3. Refresh tools in the UI or restart the server

### Add MCP Servers

1. Click the **MCP** tab in the sidebar
2. Click **➕ Add MCP Server**
3. Fill in:
   - Name: `filesystem`
   - Command: `npx`
   - Args: `-y,@modelcontextprotocol/server-filesystem,./workspace`
4. Click **Add Server**

### Customize Instructions

1. Click the **Config** tab
2. Enter custom instructions in the textarea
3. Click **Update Instructions**

## 🐛 Troubleshooting

### "Module not found" errors

```bash
pip install --upgrade -r requirements.txt
```

### "Connection refused"

Check if the port is already in use:
```bash
lsof -i :8000
```

Use a different port:
```bash
PORT=8080 python server.py
```

### "API key not found"

Make sure your `.env` file contains:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### MCP Server issues

Make sure Node.js is installed:
```bash
node --version
npm --version
```

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **API Reference**: See [README.md#api-reference](README.md#api-reference)
- **DeepAgent Docs**: https://docs.langchain.com/oss/python/deepagents/overview

## 💡 Tips

1. **Use streaming** for long-running tasks
2. **Add custom tools** for specialized functionality
3. **Enable MCP servers** for dynamic capabilities
4. **Monitor the console** for detailed execution logs
5. **Try deep research** for complex multi-step tasks

## 🎉 You're Ready!

Start chatting with your AI agent and explore its capabilities!

Need help? Check the [README.md](README.md) or open an issue.