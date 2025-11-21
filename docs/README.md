# DeepAgent Server Documentation

A production-ready AI agentic server with free web search, deep research, MCP support, and Google Sheets integration.

## 📚 Documentation Index

- **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes
- **[Google Sheets Integration](GOOGLE_SHEETS.md)** - Connect and search Google Sheets
- **[API Reference](API.md)** - REST and WebSocket endpoints
- **[Deployment](DEPLOYMENT.md)** - Production deployment guide

## 🌟 Key Features

- **Free Web Search** - DuckDuckGo integration (no API key)
- **Deep Research** - Multi-agent research with critique loops
- **MCP Support** - Dynamic tool discovery
- **Custom Tools** - Easy Python-based tool creation
- **Google Sheets** - OAuth integration with search tools
- **Streaming** - Real-time WebSocket responses
- **Web UI** - Modern interface (Gradio + built-in)

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# Run
python server.py
```

Open http://localhost:8000

## 📁 Project Structure

```
.
├── server.py                    # Main FastAPI server
├── gradio_ui.py                # Gradio interface
├── google_sheets_auth.py       # OAuth manager
├── custom_tools/               # Custom tool definitions
│   ├── google_sheets_tools.py
│   └── example_tools.py
├── requirements.txt            # Dependencies
├── .env                        # Configuration
└── docs/                       # Documentation
```

## 🔧 Configuration

Edit `.env`:

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Model
MODEL=anthropic:claude-sonnet-4-20250514

# API Keys
ANTHROPIC_API_KEY=your_key_here
```

## 🛠️ Adding Custom Tools

Create `custom_tools/my_tools.py`:

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"
```

Restart server - tools auto-load.

## 📡 API Endpoints

- `POST /api/chat` - Chat with streaming
- `GET /api/tools` - List available tools
- `GET /api/health` - Health check
- `WS /ws/chat` - WebSocket chat

See [API Reference](API.md) for details.

## 🔐 Security

- API keys in `.env` (gitignored)
- OAuth tokens in `google_sheets_tokens.json` (gitignored)
- Read-only Google Sheets access by default
- MCP servers run in isolated processes

## 🐛 Troubleshooting

**Module not found:**
```bash
pip install --upgrade -r requirements.txt
```

**Port in use:**
```bash
PORT=8080 python server.py
```

**Google Sheets not working:**
- Complete OAuth in Gradio UI
- Check `client_secrets.json` exists
- Verify Google Sheets API is enabled

## 📚 Learn More

- [DeepAgent Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain](https://docs.langchain.com)
- [MCP Servers](https://mcp.so)

## 📄 License

MIT License
