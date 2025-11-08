# DeepAgent Server

A production-ready AI agentic server built with the DeepAgent library, featuring free web search, deep research capabilities, MCP server support, custom tools integration, and a beautiful web UI.

![DeepAgent Server](https://img.shields.io/badge/DeepAgent-v1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### Core Capabilities
- **🔍 Free Web Search**: DuckDuckGo integration (no API key required)
- **📊 Deep Research**: Multi-agent research system with critique loops
- **🔌 MCP Server Support**: Dynamic tool discovery via Model Context Protocol
- **🛠️ Custom Tools**: Easy Python-based tool creation and hot-reloading
- **💬 Streaming Responses**: Real-time response streaming via WebSocket
- **🎨 Beautiful Web UI**: Modern, responsive interface for easy interaction

### Advanced Features
- **Subagent Architecture**: Specialized agents for research and critique
- **Virtual Filesystem**: Built-in file management for context isolation
- **Planning Tools**: Automatic task decomposition and planning
- **Multi-Model Support**: Works with Claude, GPT-4, Ollama, and more
- **REST API**: Full API for programmatic access
- **Configuration Management**: Web-based configuration interface

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js (for MCP servers, optional)
- Anthropic API key (or OpenAI/Ollama)

### Installation

1. **Clone or download the files**

```bash
# Create project directory
mkdir deepagent-server
cd deepagent-server
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# Required: ANTHROPIC_API_KEY
nano .env
```

4. **Run the server**

```bash
python server.py
```

5. **Open the web UI**

Navigate to: `http://localhost:8000`

## 📋 Configuration

### Environment Variables

Edit the `.env` file to configure:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000

# Model selection
MODEL=anthropic:claude-sonnet-4-20250514

# API keys
ANTHROPIC_API_KEY=your_key_here
```

### Supported Models

- **Claude** (recommended): `anthropic:claude-sonnet-4-20250514`
- **GPT-4**: `openai:gpt-4o`
- **Ollama**: `ollama:llama3.1` (requires local Ollama)

## 🛠️ Adding Custom Tools

### Method 1: Using the Custom Tools Directory

1. Create a new Python file in `custom_tools/`:

```python
# custom_tools/my_tools.py
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """Brief description of what this tool does."""
    # Your implementation
    return f"Processed: {param}"
```

2. Restart the server or click "Refresh Tools" in the UI

### Method 2: Adding Tools to server.py

Edit `server.py` and add your tool to the built-in tools section:

```python
@tool
def weather_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city."""
    # Implementation
    return "Weather data..."
```

## 🔌 MCP Server Integration

### What is MCP?

Model Context Protocol (MCP) enables dynamic tool discovery. Add MCP servers to give your agent access to:
- GitHub APIs
- Google Drive
- Slack
- File systems
- Databases
- 100+ community servers

### Adding MCP Servers

#### Via Web UI:

1. Click the **MCP** tab in the sidebar
2. Click **➕ Add MCP Server**
3. Fill in the configuration
4. Enable the server

#### Via Configuration File:

Edit `mcp_config.json`:

```json
{
  "mcp_servers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token"
      },
      "enabled": true
    }
  }
}
```

### Popular MCP Servers

- **Filesystem**: `@modelcontextprotocol/server-filesystem`
- **GitHub**: `@modelcontextprotocol/server-github`
- **Google Drive**: `@modelcontextprotocol/server-gdrive`
- **Slack**: `@modelcontextprotocol/server-slack`

Browse more at: https://mcp.so

## 📡 API Reference

### Chat Endpoint

```bash
POST /api/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "What is quantum computing?"}
  ],
  "stream": true
}
```

### WebSocket Chat

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.send(JSON.stringify({
  messages: [
    {role: "user", content: "Hello!"}
  ]
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

### Configuration Endpoints

```bash
# Get current configuration
GET /api/config

# Update configuration
POST /api/config
Content-Type: application/json

{
  "instructions": "Custom instructions...",
  "enable_research": true
}
```

### MCP Management

```bash
# List MCP servers
GET /api/mcp/servers

# Add MCP server
POST /api/mcp/servers/{server_name}
Content-Type: application/json

{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "enabled": true
}

# Delete MCP server
DELETE /api/mcp/servers/{server_name}
```

### Tools

```bash
# List available tools
GET /api/tools
```

## 🎯 Usage Examples

### Basic Chat

```
User: What are the latest developments in quantum computing?

Agent: I'll search for the latest information...
[Uses duckduckgo_search]
[Researches multiple sources]
[Synthesizes information]

Here's what I found about recent quantum computing developments...
```

### Deep Research

```
User: Write a comprehensive report on AI safety, covering current approaches, challenges, and future directions.

Agent: I'll conduct deep research on this topic...
[Creates research plan]
[Delegates to research-agent for each subtopic]
[Saves findings to files]
[Uses critique-agent for quality review]
[Refines and synthesizes]

Here's the comprehensive report...
```

### Using Custom Tools

```
User: Calculate the distance between New York (40.7128°N, 74.0060°W) and London (51.5074°N, 0.1278°W)

Agent: [Uses calculate_distance tool]
The distance between New York and London is approximately 5,570 km.
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI (React)                       │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Server                           │
├─────────────────────────────────────────────────────────────┤
│                    Agent Manager                            │
├──────────────┬────────────────┬─────────────────────────────┤
│   Built-in   │    Custom      │        MCP              │
│    Tools     │    Tools       │       Servers           │
├──────────────┴────────────────┴─────────────────────────────┤
│                    DeepAgent Core                           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐                  │
│  │Research │  │Critique │  │  Main    │                  │
│  │ Agent   │  │ Agent   │  │  Agent   │                  │
│  └─────────┘  └─────────┘  └──────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                    LangChain / LangGraph                    │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Advanced Configuration

### Custom Instructions

Customize the agent's behavior via the web UI or API:

```python
instructions = """
You are a specialized financial analyst assistant.

WORKFLOW:
1. Use web search for latest market data
2. Analyze trends using custom financial tools
3. Save detailed analysis to files
4. Provide concise summaries

Always cite your sources and indicate when data is real-time vs historical.
"""
```

### Subagent Customization

Edit `server.py` to customize subagents:

```python
custom_subagent = {
    "name": "financial-analyst",
    "description": "Analyzes financial data and market trends",
    "prompt": "You are a financial analyst...",
    "tools": ["duckduckgo_search", "calculator"],
    "model": "anthropic:claude-3-5-haiku-20241022"  # Cheaper model
}
```

### Cost Optimization

1. **Use cheaper models for subagents**: Assign Haiku to simple subagents
2. **Limit tool count**: Keep tools under 15 per agent
3. **Enable context caching**: Automatically enabled for Anthropic
4. **Set max steps**: Prevent infinite loops

```python
agent = create_deep_agent(
    tools=tools,
    instructions=instructions,
    max_steps=20  # Limit execution steps
)
```

## 🐛 Troubleshooting

### Common Issues

**"No module named 'deepagents'"**
```bash
pip install --upgrade deepagents
```

**"ANTHROPIC_API_KEY not found"**
```bash
# Ensure .env file exists and contains your key
echo "ANTHROPIC_API_KEY=your_key" > .env
```

**"MCP server failed to start"**
```bash
# Ensure Node.js is installed
node --version

# Install MCP server globally
npx -y @modelcontextprotocol/server-filesystem
```

**"Connection refused on port 8000"**
```bash
# Check if port is in use
lsof -i :8000

# Use different port
PORT=8080 python server.py
```

### Debug Mode

Enable detailed logging:

```bash
# Add to .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=deepagent-debug
```

## 📊 Performance Tips

1. **Use streaming for long-running tasks**: Provides real-time feedback
2. **Limit research depth**: Set clear stopping conditions
3. **Monitor token usage**: Use LangSmith for tracking
4. **Cache prompts**: Anthropic automatically caches system prompts
5. **Optimize tool descriptions**: Keep under 2 lines

## 🔒 Security Considerations

- **API Keys**: Never commit `.env` files to version control
- **MCP Servers**: Only enable trusted MCP servers
- **Custom Tools**: Validate all inputs in custom tools
- **Production Deployment**: Use reverse proxy (nginx) and HTTPS

## 🚢 Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```

```bash
docker build -t deepagent-server .
docker run -p 8000:8000 --env-file .env deepagent-server
```

### Using systemd

```bash
# Create service file
sudo nano /etc/systemd/system/deepagent.service
```

```ini
[Unit]
Description=DeepAgent Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/deepagent-server
EnvironmentFile=/path/to/deepagent-server/.env
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable deepagent
sudo systemctl start deepagent
```

## 📚 Additional Resources

- **DeepAgent Documentation**: https://docs.langchain.com/oss/python/deepagents/overview
- **LangChain Docs**: https://docs.langchain.com
- **MCP Servers**: https://mcp.so
- **DuckDuckGo Search**: https://github.com/deedy5/duckduckgo_search

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional built-in tools
- More MCP server examples
- UI enhancements
- Performance optimizations
- Documentation improvements

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [DeepAgent](https://github.com/langchain-ai/deepagents) by LangChain AI
- Uses [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search) for free web search
- Inspired by Claude Code and Deep Research architectures

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the DeepAgent documentation

---

**Happy Building! 🚀**