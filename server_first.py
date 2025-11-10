"""
DeepAgent Server - AI Agentic Server with Web UI
Features: Web search, Deep research, MCP server support, Custom tools, Streaming responses
Supported Models: Claude (Anthropic), GPT-4 (OpenAI), Gemini (Google), Ollama (Local)
"""
import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Server configuration"""
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-4-20250514")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # MCP configuration file path
    MCP_CONFIG_FILE = os.getenv("MCP_CONFIG_FILE", "mcp_config.json")
    
    # Custom tools directory
    CUSTOM_TOOLS_DIR = os.getenv("CUSTOM_TOOLS_DIR", "custom_tools")

config = Config()

# ============================================================================
# BUILT-IN TOOLS
# ============================================================================

# Initialize DuckDuckGo search tool (working version)
duckduckgo_search = DuckDuckGoSearchRun()

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# CUSTOM TOOLS LOADER
# ============================================================================

class CustomToolsLoader:
    """Load custom tools from Python files"""
    
    @staticmethod
    def load_tools_from_directory(directory: str) -> List[Any]:
        """
        Load custom tools from Python files in a directory.
        Each file should define functions with @tool decorator.
        """
        tools = []
        
        if not os.path.exists(directory):
            os.makedirs(directory)
            # Create example tool file
            example_tool = '''"""
Example custom tool
Define your tools here using @tool decorator
"""
from langchain_core.tools import tool

@tool
def example_calculator(a: float, b: float, operation: str = "add") -> float:
    """
    Perform basic arithmetic operations.
    
    Args:
        a: First number
        b: Second number
        operation: Operation to perform (add, subtract, multiply, divide)
    
    Returns:
        Result of the operation
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return a / b
    else:
        return "Error: Unknown operation"
'''
            with open(os.path.join(directory, "example_tools.py"), "w") as f:
                f.write(example_tool)
        
        # Import tools from Python files
        import sys
        import importlib.util
        
        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(directory, filename)
                
                try:
                    # Load module
                    spec = importlib.util.spec_from_file_location(
                        filename[:-3], filepath
                    )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[filename[:-3]] = module
                    spec.loader.exec_module(module)
                    
                    # Extract tools
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if hasattr(attr, "name") and hasattr(attr, "description"):
                            tools.append(attr)
                            print(f"Loaded custom tool: {attr.name}")
                
                except Exception as e:
                    print(f"Error loading tools from {filename}: {e}")
        
        return tools


# ============================================================================
# MCP CONFIGURATION MANAGER
# ============================================================================

class MCPConfigManager:
    """Manage MCP server configurations"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "mcp_servers": {
                    "example_filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
                        "transport": "stdio",
                        "enabled": False
                    }
                }
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save MCP configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def get_enabled_servers(self) -> Dict[str, Any]:
        """Get only enabled MCP servers"""
        mcp_servers = self.config.get("mcp_servers", {})
        enabled_servers = {}
        for name, config in mcp_servers.items():
            if config.get("enabled", False):
                # Remove 'enabled' field before passing to MCP client
                server_config = {k: v for k, v in config.items() if k != "enabled"}
                enabled_servers[name] = server_config
        return enabled_servers


# ============================================================================
# AGENT MANAGER
# ============================================================================

class AgentManager:
    """Manage DeepAgent instances"""
    
    def __init__(self):
        self.mcp_config_manager = MCPConfigManager(config.MCP_CONFIG_FILE)
        self.custom_tools_loader = CustomToolsLoader()
        self.agent = None
        self.mcp_client = None
    
    async def initialize_agent(
        self,
        instructions: Optional[str] = None,
        enable_research: bool = True
    ):
        """Initialize the DeepAgent with all tools and configurations"""
        
        # Built-in tools
        tools = [
            duckduckgo_search,
            get_current_time
        ]
        
        # Load custom tools
        custom_tools = self.custom_tools_loader.load_tools_from_directory(
            config.CUSTOM_TOOLS_DIR
        )
        tools.extend(custom_tools)
        
        # Load MCP tools and wrap them to save large responses
        enabled_mcp_servers = self.mcp_config_manager.get_enabled_servers()
        print(f"Enabled MCP servers: {list(enabled_mcp_servers.keys())}")
        if enabled_mcp_servers:
            try:
                from langchain_mcp_adapters.client import MultiServerMCPClient
                from langchain_core.tools import StructuredTool
                import json
                
                print("Creating MCP client...")
                self.mcp_client = MultiServerMCPClient(enabled_mcp_servers)
                print("Getting MCP tools...")
                mcp_tools = await self.mcp_client.get_tools()
                
                # Wrap each MCP tool to save large responses
                def wrap_mcp_tool(original_tool):
                    """Wrap tool to save large responses to files"""
                    original_func = original_tool.coroutine if hasattr(original_tool, 'coroutine') else original_tool.func
                    
                    async def wrapped_func(*args, **kwargs):
                        # Call original tool
                        if asyncio.iscoroutinefunction(original_func):
                            result = await original_func(*args, **kwargs)
                        else:
                            result = original_func(*args, **kwargs)
                            if asyncio.iscoroutine(result):
                                result = await result
                        
                        # Check if response is large
                        result_str = str(result)
                        if len(result_str) > 10000:
                            # Save to file for debugging/logging purposes
                            os.makedirs("mcp_output", exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"mcp_output/{original_tool.name}_{timestamp}.json"
                            
                            with open(filename, 'w') as f:
                                try:
                                    if isinstance(result, (dict, list)):
                                        json.dump(result, f, indent=2)
                                    else:
                                        f.write(result_str)
                                except:
                                    f.write(result_str)
                            
                            print(f"[BACKGROUND] Saved large {original_tool.name} response ({len(result_str)} chars) to {filename}")
                            
                            # Return a smart truncated version that the agent can actually use
                            # Extract key information if it's JSON
                            if isinstance(result, dict):
                                # For dict results, return a summarized version
                                summary = {k: v for k, v in list(result.items())[:20]}  # First 20 keys
                                truncated = json.dumps(summary, indent=2)[:3000]
                                return f"{truncated}\n\n... (Response truncated - showing first portion of data. Total size: {len(result_str)} chars)"
                            elif isinstance(result, list):
                                # For list results, return first few items
                                summary = result[:5]  # First 5 items
                                truncated = json.dumps(summary, indent=2)[:3000]
                                return f"{truncated}\n\n... (Response truncated - showing first {len(summary)} items. Total items: {len(result)})"
                            else:
                                # For string results, return first portion
                                truncated = result_str[:3000]
                                return f"{truncated}\n\n... (Response truncated. Total size: {len(result_str)} chars)"
                        
                        return result
                    
                    # Return wrapped tool
                    return StructuredTool(
                        name=original_tool.name,
                        description=original_tool.description,
                        coroutine=wrapped_func,
                        args_schema=original_tool.args_schema
                    )
                
                # Wrap all MCP tools
                wrapped_tools = [wrap_mcp_tool(tool) for tool in mcp_tools]
                tools.extend(wrapped_tools)
                
                print(f"Loaded and wrapped {len(mcp_tools)} MCP tools from {len(enabled_mcp_servers)} servers")
                print(f"MCP tool names: {[t.name for t in mcp_tools]}")
            except ImportError:
                print("Warning: langchain-mcp-adapters not installed. MCP support disabled.")
                print("Install with: pip install langchain-mcp-adapters")
            except Exception as e:
                print(f"Error loading MCP tools: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No enabled MCP servers found in config")
        
        # Define subagents for deep research
        subagents = []
        if enable_research:
            research_sub_agent = {
                "name": "research-agent",
                "description": "Conducts detailed research on specific topics using web search",
                "system_prompt": """You are a dedicated researcher.
Your job is to conduct thorough research based on the assigned topic.
Use duckduckgo_search to find relevant information.
Save your findings to files for reference.
Only your FINAL answer will be passed back to the main agent.""",
                "tools": [duckduckgo_search]  # Pass actual tool objects, not strings
            }
            
            critique_sub_agent = {
                "name": "critique-agent",
                "description": "Reviews and critiques reports and research outputs",
                "system_prompt": """You are a dedicated editor and critic.
Review the report or output provided to you.
Provide constructive feedback on accuracy, completeness, and clarity.
Be specific about what needs improvement."""
                # No tools needed for critique agent
            }
            
            subagents = [research_sub_agent, critique_sub_agent]
        
        # Default instructions
        if instructions is None:
            instructions = """You are an expert AI assistant with access to web search, MCP tools, and file operations.

CAPABILITIES:
- Web search using DuckDuckGo (free, no API key needed)
- MCP tools for database operations, APIs, and integrations
- File operations (write_file, read_file, edit_file, ls, grep_search, glob_search)
- Deep research using specialized research agents
- Custom tools for specialized tasks

IMPORTANT: HANDLING LARGE DATA RESPONSES
When MCP tools return very large data (>10k chars), you will receive a truncated but usable portion:
- For JSON objects: First 20 keys with their values
- For JSON arrays: First 5 items
- For text: First 3000 characters

This truncated data is COMPLETE and USABLE for analysis. You should:
✅ Analyze the truncated data directly - it contains the key information
✅ Extract relevant information from what you received
✅ Answer the user's question based on the data provided
✅ If you see "Response truncated", that's normal - work with what you have

DO NOT:
❌ Try to call the same tool again to get "full" data
❌ Try to read files or search for more data
❌ Get stuck in loops

The truncation is intelligent - it gives you the most important parts of the response.

WORKFLOW FOR DATABASE/MCP TASKS:
1. Call the MCP tool to get data
2. Analyze the data returned (even if truncated)
3. Extract the information needed to answer the question
4. Provide a clear answer to the user
5. Move on to the next task

WORKFLOW FOR RESEARCH TASKS:
1. Break complex questions into sub-topics
2. Use research-agent for deep investigation of each topic
3. Save findings to files (e.g., research_topic1.md)
4. Synthesize information into a comprehensive answer
5. Use critique-agent to review quality
6. Refine based on feedback

Always use web search for current information and events.
Be thorough but concise in your final answers."""
        
        # Create agent
        print(f"Creating agent with model: {config.MODEL}")
        print(f"Number of tools: {len(tools)}")
        print(f"Tool names: {[t.name for t in tools]}")
        
        self.agent = create_deep_agent(
            tools=tools,
            system_prompt=instructions,
            subagents=subagents,
            model=config.MODEL,
            debug=True
        )
     
        
        print(f"Agent initialized with {len(tools)} tools and {len(subagents)} subagents")
        
        return self.agent
    
    async def get_agent(self):
        """Get or initialize agent"""
        if self.agent is None:
            await self.initialize_agent()
        return self.agent
    
    async def reinitialize_agent(self, instructions: Optional[str] = None):
        """Reinitialize agent (useful after config changes)"""
        self.agent = None
        if self.mcp_client:
            # Clean up old MCP client if exists
            self.mcp_client = None
        return await self.initialize_agent(instructions)


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="DeepAgent Server",
    description="AI Agentic Server with Web UI, Free Search, Deep Research, and MCP Support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent manager
agent_manager = AgentManager()


# ============================================================================
# API MODELS
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = True
    enable_research: bool = True


class ConfigRequest(BaseModel):
    instructions: Optional[str] = None
    enable_research: bool = True


class MCPServerConfig(BaseModel):
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Serve the web UI"""
    return HTMLResponse(content=open("index.html").read())


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming support
    """
    try:
        agent = await agent_manager.get_agent()
        
        # Convert messages to agent format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        if request.stream:
            async def generate():
                try:
                    async for chunk in agent.astream(
                        {"messages": messages},
                        stream_mode="values"
                    ):
                        if "messages" in chunk and chunk["messages"]:
                            last_message = chunk["messages"][-1]
                            if hasattr(last_message, 'content'):
                                yield f"data: {json.dumps({'content': str(last_message.content), 'done': False})}\n\n"
                    
                    yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            result = await agent.ainvoke({"messages": messages})
            return {
                "response": result["messages"][-1].content,
                "done": True
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat
    """
    await websocket.accept()
    
    try:
        agent = await agent_manager.get_agent()
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            messages = data.get("messages", [])
            
            # Stream response
            async for chunk in agent.astream(
                {"messages": messages},
                stream_mode="values"
            ):
                if "messages" in chunk and chunk["messages"]:
                    last_message = chunk["messages"][-1]
                    if hasattr(last_message, 'content'):
                        await websocket.send_json({
                            "type": "message",
                            "content": str(last_message.content),
                            "done": False
                        })
            
            # Send completion signal
            await websocket.send_json({
                "type": "message",
                "content": "",
                "done": True
            })
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })
        await websocket.close()


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "model": config.MODEL,
        "mcp_config": agent_manager.mcp_config_manager.config,
        "custom_tools_dir": config.CUSTOM_TOOLS_DIR
    }


@app.post("/api/config")
async def update_config(request: ConfigRequest):
    """Update agent configuration"""
    try:
        await agent_manager.reinitialize_agent(
            instructions=request.instructions
        )
        return {"status": "success", "message": "Agent reinitialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp/servers")
async def get_mcp_servers():
    """Get MCP server configurations"""
    return agent_manager.mcp_config_manager.config.get("mcp_servers", {})


@app.post("/api/mcp/servers/{server_name}")
async def add_mcp_server(server_name: str, server_config: MCPServerConfig):
    """Add or update MCP server configuration"""
    try:
        current_config = agent_manager.mcp_config_manager.config
        
        if "mcp_servers" not in current_config:
            current_config["mcp_servers"] = {}
        
        current_config["mcp_servers"][server_name] = {
            "command": server_config.command,
            "args": server_config.args,
            "env": server_config.env or {},
            "enabled": server_config.enabled
        }
        
        agent_manager.mcp_config_manager.save_config(current_config)
        
        # Reinitialize agent to load new MCP server
        if server_config.enabled:
            await agent_manager.reinitialize_agent()
        
        return {"status": "success", "message": f"MCP server '{server_name}' configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/mcp/servers/{server_name}")
async def delete_mcp_server(server_name: str):
    """Delete MCP server configuration"""
    try:
        current_config = agent_manager.mcp_config_manager.config
        
        if "mcp_servers" in current_config and server_name in current_config["mcp_servers"]:
            del current_config["mcp_servers"][server_name]
            agent_manager.mcp_config_manager.save_config(current_config)
            
            # Reinitialize agent
            await agent_manager.reinitialize_agent()
            
            return {"status": "success", "message": f"MCP server '{server_name}' deleted"}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    """List all available tools"""
    agent = await agent_manager.get_agent()
    
    tools_info = []
    for tool in agent.tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
        })
    
    return {"tools": tools_info}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent_manager.agent is not None,
        "model": config.MODEL
    }


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    print("Initializing DeepAgent server...")
    await agent_manager.initialize_agent()
    print("Server ready!")


if __name__ == "__main__":
    import uvicorn
    
    print(f"""
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
║  Starting on: http://{config.HOST}:{config.PORT}                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )