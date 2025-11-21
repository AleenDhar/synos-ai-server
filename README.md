# DeepAgent Server

A production-ready AI agentic server with free web search, deep research, MCP support, custom tools, and Google Sheets integration.

![DeepAgent Server](https://img.shields.io/badge/DeepAgent-v1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

- **🔍 Free Web Search** - DuckDuckGo integration (no API key)
- **📊 Deep Research** - Multi-agent research with critique loops
- **🔌 MCP Support** - Dynamic tool discovery
- **🛠️ Custom Tools** - Easy Python-based tool creation
- **📊 Google Sheets** - OAuth integration with search tools
- **💬 Streaming** - Real-time WebSocket responses
- **🎨 Web UI** - Modern interface (Gradio + built-in)

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run
python server.py
```

Open http://localhost:8000

**📚 [Full Documentation](docs/README.md)**

## 📋 Configuration

Edit `.env`:

```bash
HOST=0.0.0.0
PORT=8000
MODEL=anthropic:claude-sonnet-4-20250514
ANTHROPIC_API_KEY=your_key_here
```

**Supported Models:** Claude, GPT-4, Gemini, Ollama

## 🛠️ Custom Tools

Create `custom_tools/my_tools.py`:

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"
```

Restart server - tools auto-load.

## 🔌 MCP Servers

Add MCP servers via web UI or edit `mcp_config.json`:

```json
{
  "mcp_servers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "token"},
      "enabled": true
    }
  }
}
```

Browse servers at https://mcp.so

## 📡 API

```bash
POST /api/chat          # Chat with streaming
GET  /api/tools         # List tools
GET  /api/health        # Health check
WS   /ws/chat          # WebSocket chat
```

**[Full API Reference](docs/API.md)**

## 📊 Google Sheets Integration

Connect Google Sheets with OAuth:

```bash
# Start with UI
./start_with_ui.sh

# Open http://localhost:7860
# Go to "Google Sheets Setup" tab
# Click "Connect Google Sheets"
```

Then search sheets:
```
"Find 'john' in sheet: YOUR_SHEET_ID"
```

**[Google Sheets Guide](docs/GOOGLE_SHEETS.md)**

## 🐛 Troubleshooting

**Module not found:**
```bash
pip install --upgrade -r requirements.txt
```

**Port in use:**
```bash
PORT=8080 python server.py
```

**API key not found:**
Ensure `.env` contains `ANTHROPIC_API_KEY=sk-ant-...`

**MCP server failed:**
```bash
node --version  # Ensure Node.js installed
```

## 🚢 Deployment

**[Deployment Guide](docs/DEPLOYMENT.md)** - Docker, systemd, nginx, scaling

## 📚 Resources

- [DeepAgent Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain](https://docs.langchain.com)
- [MCP Servers](https://mcp.so)

## 📄 License

MIT License

---

Built with [DeepAgent](https://github.com/langchain-ai/deepagents) by LangChain AI