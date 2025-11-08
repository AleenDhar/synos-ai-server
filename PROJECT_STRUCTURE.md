# 📁 Project Structure

## Overview

```
deepagent-server/
├── server.py                 # Main FastAPI server
├── index.html               # Web UI
├── start.sh                 # Startup script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .env                     # Environment variables (create from .example)
├── mcp_config.json         # MCP server configurations
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Docker ignore patterns
├── .gitignore             # Git ignore patterns
├── README.md              # Full documentation
├── QUICKSTART.md          # Quick start guide
├── PROJECT_STRUCTURE.md   # This file
├── custom_tools/          # Custom tools directory
│   └── example_tools.py   # Example custom tools
└── workspace/             # Agent workspace (auto-created)
```

## File Descriptions

### Core Files

#### `server.py`
The main server application containing:
- **FastAPI setup**: Web server and API endpoints
- **Agent Manager**: Manages DeepAgent lifecycle
- **Built-in Tools**: DuckDuckGo search, time, news
- **Custom Tools Loader**: Dynamically loads tools from `custom_tools/`
- **MCP Integration**: Connects to MCP servers
- **API Endpoints**: REST and WebSocket endpoints
- **Configuration Management**: Handles settings and updates

Key components:
```python
- Config class: Environment configuration
- Built-in tools: duckduckgo_search, duckduckgo_news, get_current_time
- CustomToolsLoader: Loads tools from Python files
- MCPConfigManager: Manages MCP server configs
- AgentManager: Initializes and manages agents
- FastAPI app: Serves UI and API
```

#### `index.html`
Single-page web application with:
- **Modern UI**: Clean, responsive interface
- **Real-time Chat**: Streaming message display
- **Configuration Panel**: Manage settings via UI
- **MCP Management**: Add/remove MCP servers
- **Tools View**: See available tools
- **Tabs**: Config, MCP, Tools sections

Features:
- WebSocket and REST API support
- Auto-scrolling chat
- Typing indicators
- Message formatting
- Export chat functionality

### Configuration Files

#### `.env` / `.env.example`
Environment variables:
```bash
HOST=0.0.0.0                                    # Server host
PORT=8000                                        # Server port
MODEL=anthropic:claude-sonnet-4-20250514        # AI model
ANTHROPIC_API_KEY=your_key_here                 # API key
CUSTOM_TOOLS_DIR=custom_tools                   # Tools directory
MCP_CONFIG_FILE=mcp_config.json                 # MCP config path
```

#### `mcp_config.json`
MCP server configurations:
```json
{
  "mcp_servers": {
    "server_name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {"KEY": "value"},
      "enabled": true
    }
  }
}
```

#### `requirements.txt`
Python dependencies:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `deepagents`: Agent framework
- `duckduckgo-search`: Free web search
- `langchain-mcp-adapters`: MCP support
- Plus LangChain ecosystem packages

### Scripts

#### `start.sh`
Automated startup script that:
1. Checks Python version
2. Creates virtual environment
3. Installs dependencies
4. Validates configuration
5. Starts the server

Usage:
```bash
chmod +x start.sh
./start.sh
```

### Docker Files

#### `Dockerfile`
Container image definition:
- Base: `python:3.11-slim`
- Installs: Python deps + Node.js (for MCP)
- Exposes: Port 8000
- Health check: `/api/health`

Build:
```bash
docker build -t deepagent-server .
```

#### `docker-compose.yml`
Multi-container orchestration:
- Service: deepagent
- Volumes: custom_tools, workspace, config
- Networking: isolated network
- Restart: unless-stopped

Run:
```bash
docker-compose up -d
```

### Custom Tools Directory

#### `custom_tools/`
Directory for custom tool definitions.

Each Python file can define multiple tools:
```python
# custom_tools/my_tools.py
from langchain_core.tools import tool

@tool
def my_function(param: str) -> str:
    """Tool description."""
    return "result"
```

**Auto-loading**: Server automatically discovers and loads all tools from this directory.

**Naming**: Use descriptive filenames like:
- `financial_tools.py`
- `data_analysis.py`
- `api_integrations.py`

#### `example_tools.py`
Provided example tools:
- `calculator`: Basic arithmetic
- `calculate_percentage`: Percentage calculations
- `convert_temperature`: Temperature conversion
- `text_statistics`: Text analysis
- `generate_uuid`: UUID generation
- `encode_base64` / `decode_base64`: Base64 encoding
- `calculate_distance`: Geographic distance
- `json_formatter`: JSON formatting

### Workspace Directory

#### `workspace/`
**Auto-created** directory for agent file operations.

The agent uses this as a virtual filesystem to:
- Save research findings
- Store intermediate results
- Manage large content
- Organize planning documents

**Note**: This directory is gitignored and can be cleaned periodically.

## File Flow

### Request Flow

```
User Browser
    ↓
index.html (UI)
    ↓
WebSocket/REST API
    ↓
server.py (FastAPI)
    ↓
AgentManager
    ↓
DeepAgent
    ↓
Tools (Built-in + Custom + MCP)
    ↓
LLM (Claude/GPT/Ollama)
    ↓
Response Stream
    ↓
User Browser
```

### Tool Loading Flow

```
Server Startup
    ↓
AgentManager.initialize_agent()
    ↓
┌─────────────┬─────────────┬─────────────┐
│  Built-in   │   Custom    │     MCP     │
│   Tools     │   Tools     │   Servers   │
└─────────────┴─────────────┴─────────────┘
         ↓
    Combined Tool List
         ↓
    create_deep_agent(tools=...)
         ↓
    Agent Ready
```

### Configuration Update Flow

```
UI Config Change
    ↓
POST /api/config
    ↓
AgentManager.reinitialize_agent()
    ↓
Load new tools/config
    ↓
Create new agent instance
    ↓
Return success
```

## Key Design Patterns

### 1. Single Responsibility
Each file has a clear, focused purpose:
- `server.py`: Server and orchestration only
- `index.html`: UI only
- `example_tools.py`: Tool definitions only

### 2. Hot Reloading
- Custom tools: Auto-discovered on startup
- MCP servers: Dynamically loaded
- Config: Can be updated via API

### 3. Separation of Concerns
- **Configuration**: Environment variables and JSON
- **Business Logic**: server.py
- **Presentation**: index.html
- **Tools**: Separate directory

### 4. Extensibility
Easy to extend:
- Add tools: Drop Python file in `custom_tools/`
- Add MCP server: Update `mcp_config.json`
- Customize UI: Edit `index.html`
- Add API endpoints: Add routes in `server.py`

## Environment-Specific Files

### Development
```
.env              # Local API keys
workspace/        # Test data
custom_tools/     # Development tools
```

### Production
```
.env.production   # Production keys
docker-compose.yml # Container config
Dockerfile        # Image definition
```

## Security Considerations

### Sensitive Files (Never Commit)
- `.env`: Contains API keys
- `mcp_config.json`: May contain tokens
- `workspace/`: May contain user data

### Safe to Commit
- `.env.example`: Template only
- `server.py`: No secrets
- `index.html`: Client-side code
- `requirements.txt`: Public packages
- Documentation files

## Maintenance

### Regular Tasks
1. **Update dependencies**: `pip install --upgrade -r requirements.txt`
2. **Clean workspace**: `rm -rf workspace/*`
3. **Review tools**: Check `custom_tools/` for unused tools
4. **Monitor logs**: Check server output for errors

### Backup Important Files
- `custom_tools/`: Your custom tool implementations
- `.env`: Configuration (if not using secrets manager)
- `mcp_config.json`: MCP server setups

## Adding New Features

### Add a Built-in Tool
1. Edit `server.py`
2. Add `@tool` decorated function
3. Add to tools list in `initialize_agent()`
4. Restart server

### Add Custom Tool
1. Create file in `custom_tools/`
2. Define `@tool` decorated functions
3. Server auto-loads on startup
4. Or click "Refresh Tools" in UI

### Add API Endpoint
1. Edit `server.py`
2. Add `@app.get/post/put/delete` decorated function
3. Implement logic
4. Update UI to call new endpoint

### Extend UI
1. Edit `index.html`
2. Add HTML elements
3. Add JavaScript functions
4. Add CSS styling
5. Refresh browser

## Dependencies Graph

```
server.py
├── fastapi (web framework)
├── deepagents (agent core)
│   ├── langchain-core
│   ├── langchain-anthropic
│   └── langgraph
├── duckduckgo-search (free search)
├── langchain-mcp-adapters (MCP support)
└── custom_tools/*.py (your tools)
```

## Performance Considerations

### File Loading
- Tools: Loaded once at startup
- MCP: Connected once, reused
- Config: Cached in memory

### Memory Usage
- Agent state: In-memory by default
- Workspace: Disk storage
- MCP connections: Persistent

### Scalability
- Single agent per server instance
- Stateless API (except WebSocket)
- Horizontal scaling: Run multiple instances behind load balancer

---

This structure is designed to be:
- ✅ **Simple**: Easy to understand and navigate
- ✅ **Modular**: Each component is independent
- ✅ **Extensible**: Easy to add new features
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Production-ready**: Docker support, health checks