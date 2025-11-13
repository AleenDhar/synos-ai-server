"""DeepAgent Server - AI Agentic Server with Web UI

Features: Web search, Deep research, MCP server support, Custom tools, Streaming responses, Headless browser control
Supported Models: Claude (Anthropic), GPT-4 (OpenAI), Gemini (Google), Ollama (Local)
"""

import asyncio
import json
import os
import logging
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

# Configure logging to suppress verbose MCP warnings
logging.getLogger("fastmcp").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)

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
        """Load custom tools from Python files in a directory.
        
        Each file should define functions with @tool decorator.
        """
        tools = []
        
        if not os.path.exists(directory):
            os.makedirs(directory)
            # Create example tool file
            example_tool = '''"""Example custom tool

Define your tools here using @tool decorator
"""
from langchain_core.tools import tool

@tool
def example_calculator(a: float, b: float, operation: str = "add") -> float:
    """Perform basic arithmetic operations.
    
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
                    spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
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
    
    async def initialize_agent(self, 
                              instructions: Optional[str] = None,
                              enable_research: bool = True,
                              model: Optional[str] = None,
                              headless: bool = True):
        """Initialize the DeepAgent with all tools and configurations"""
        
        # Built-in tools
        tools = [
            duckduckgo_search,
            get_current_time
        ]
        
        # Load custom tools
        custom_tools = self.custom_tools_loader.load_tools_from_directory(config.CUSTOM_TOOLS_DIR)
        
        # Wrap browser tools to enforce headless mode
        wrapped_custom_tools = []
        for tool in custom_tools:
            if tool.name in ['browser_research', 'browser_research_multiple', 'browser_interactive_research']:
                # Create wrapped version that automatically includes headless parameter
                original_func = tool.coroutine if hasattr(tool, 'coroutine') else tool.func
                
                def create_wrapped_browser_tool(original, headless_val):
                    async def wrapped_func(*args, **kwargs):
                        # Force headless parameter
                        kwargs['headless'] = headless_val
                        if asyncio.iscoroutinefunction(original):
                            return await original(*args, **kwargs)
                        else:
                            return original(*args, **kwargs)
                    return wrapped_func
                
                wrapped_func = create_wrapped_browser_tool(original_func, headless)
                
                from langchain_core.tools import StructuredTool
                wrapped_tool = StructuredTool(
                    name=tool.name,
                    description=tool.description + f" (Browser mode: {'headless/invisible' if headless else 'visible/slow'})",
                    coroutine=wrapped_func,
                    args_schema=tool.args_schema
                )
                wrapped_custom_tools.append(wrapped_tool)
                print(f"✓ Wrapped browser tool: {tool.name} with headless={headless}")
            else:
                wrapped_custom_tools.append(tool)
        
        tools.extend(wrapped_custom_tools)
        
        # Load MCP tools and wrap them to save large responses
        enabled_mcp_servers = self.mcp_config_manager.get_enabled_servers()
        print(f"Enabled MCP servers: {list(enabled_mcp_servers.keys())}")
        
        if enabled_mcp_servers:
            try:
                from langchain_mcp_adapters.client import MultiServerMCPClient
                from langchain_core.tools import StructuredTool
                import json
                import sys
                import io
                
                print("Creating MCP client...")
                
                # Suppress MCP schema warnings by temporarily redirecting stderr
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    self.mcp_client = MultiServerMCPClient(enabled_mcp_servers)
                    print("Getting MCP tools...")
                    mcp_tools = await self.mcp_client.get_tools()
                finally:
                    # Restore stderr
                    sys.stderr = old_stderr
                
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
                        
                        # Convert result to proper format
                        # Handle tuple results from MCP tools
                        if isinstance(result, tuple):
                            # MCP tools often return (data, metadata) tuples
                            result = result[0] if len(result) > 0 else result
                        
                        # Try to parse if it's a JSON string
                        if isinstance(result, str):
                            try:
                                result = json.loads(result)
                            except:
                                pass  # Keep as string if not JSON
                        
                        # Check if response is large
                        result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                        
                        if len(result_str) > 10000:
                            # Save to file silently (no console output)
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
                            
                            # Extract key information for preview
                            # Return actual data but truncated intelligently
                            if isinstance(result, dict):
                                # For dict, keep important fields and truncate long values
                                truncated_result = {}
                                for key, value in result.items():
                                    if isinstance(value, str) and len(value) > 200:
                                        truncated_result[key] = value[:200] + "..."
                                    else:
                                        truncated_result[key] = value
                                return truncated_result
                            
                            elif isinstance(result, list):
                                # For list, return first 5 items
                                truncated_list = []
                                for item in result[:5]:
                                    if isinstance(item, dict):
                                        truncated_item = {}
                                        for key, value in item.items():
                                            if isinstance(value, str) and len(value) > 200:
                                                truncated_item[key] = value[:200] + "..."
                                            else:
                                                truncated_item[key] = value
                                        truncated_list.append(truncated_item)
                                    else:
                                        truncated_list.append(item)
                                
                                if len(result) > 5:
                                    return truncated_list + [f"... and {len(result) - 5} more items"]
                                return truncated_list
                            
                            else:
                                # For strings, return first 2000 chars
                                return result_str[:2000] + "..." if len(result_str) > 2000 else result_str
                        
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
        
        # Default instructions with browser mode guidance
        if instructions is None:
            browser_mode = "headless=True (invisible, fast)" if headless else "headless=False (visible, slow)"
            instructions = f"""You are an expert AI assistant with access to web search, MCP tools, browser automation, and file operations.

CAPABILITIES:
- Web search using DuckDuckGo (free, no API key needed)
- Browser automation with Playwright (currently in {browser_mode} mode)
- MCP tools for database operations, APIs, and integrations
- File operations (write_file, read_file, edit_file, ls, grep_search, glob_search)
- Deep research using specialized research agents
- Custom tools for specialized tasks

🌐 BROWSER AUTOMATION INSTRUCTIONS:
- Current browser mode: {browser_mode}
- ALWAYS pass headless={headless} to browser_research and browser_research_multiple tools
- Use browser tools after max 3-5 DuckDuckGo searches (don't over-search!)
- For deep research: search → get URLs → use browser_research_multiple
- Never make more than 5 consecutive DuckDuckGo searches

🚨 CRITICAL RESPONSE RULES 🚨

1. NEVER include raw tool outputs in your response
2. NEVER paste JSON data, API responses, or database records directly
3. ALWAYS extract and summarize the key information
4. Your response should be human-readable, not machine data

CORRECT RESPONSE FORMAT:
✅ "The opportunity 'Humain_S2P' has an amount of $160,000 and closes on April 1, 2026."
✅ "I found 3 related documents: Document A, Document B, and Document C."
✅ "The account has 5 open opportunities totaling $2.5M."

INCORRECT RESPONSE FORMAT:
❌ Pasting raw JSON like: {{"attributes":{{"type":"Opportunity"}},"Id":"006P700000O0NMzIAN"...}}
❌ Pasting entire JSON objects
❌ Including raw database records
❌ Showing truncated data messages like "... (Response truncated. Total size: 38694 chars)"

WORKFLOW:
1. Call the necessary tools to get data
2. ANALYZE the data internally (don't show this to user)
3. EXTRACT the key information that answers the question
4. RESPOND with a clear, human-readable summary

HANDLING LARGE DATA:
When tools return large data (>10,000 chars), they are automatically:
1. Saved to a file in the background (you don't need to do anything)
2. Truncated intelligently to show you the key information
3. Long text fields are shortened to 200 characters

The truncated data you receive contains ALL the information you need to answer the question.
- Use the data directly - it has all key fields
- DO NOT mention truncation or saved files to the user
- DO NOT try to read saved files
- Just extract and summarize the information naturally

REMEMBER: Users want insights, not data dumps. Be conversational and helpful!"""
        
        # Use provided model or default from config
        selected_model = model or config.MODEL
        
        # Create agent
        print(f"Creating agent with model: {selected_model}")
        print(f"Number of tools: {len(tools)}")
        print(f"Tool names: {[t.name for t in tools]}")
        print(f"Browser mode: {'headless' if headless else 'visible'}")
        
        self.agent = create_deep_agent(
            tools=tools,
            system_prompt=instructions,
            subagents=subagents,
            model=selected_model,
            debug=False  # Disable debug to prevent verbose tool response logging
        )
        
        print(f"Agent initialized with {len(tools)} tools and {len(subagents)} subagents")
        return self.agent
    
    async def get_agent(self):
        """Get or initialize agent"""
        if self.agent is None:
            await self.initialize_agent()
        return self.agent
    
    async def reinitialize_agent(self, instructions: Optional[str] = None, model: Optional[str] = None, headless: bool = True):
        """Reinitialize agent (useful after config changes)"""
        self.agent = None
        if self.mcp_client:
            # Clean up old MCP client if exists
            self.mcp_client = None
        return await self.initialize_agent(instructions, model=model, headless=headless)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="DeepAgent Server",
    description="AI Agentic Server with Web UI, Free Search, Deep Research, MCP Support, and Headless Browser Control",
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
    system_prompt: Optional[str] = None
    model: Optional[str] = None  # e.g., "openai:gpt-4", "anthropic:claude-sonnet-4"
    headless: bool = True  # Browser mode: True = invisible/fast, False = visible/slow

class StructuredChatRequest(BaseModel):
    messages: List[ChatMessage]
    structured_output_format: Dict[str, Any]  # JSON schema for structured output
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    enable_research: bool = False
    headless: bool = True  # Browser mode: True = invisible/fast, False = visible/slow

class ConfigRequest(BaseModel):
    instructions: Optional[str] = None
    enable_research: bool = True
    headless: bool = True

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
    """Chat endpoint with streaming support and browser headless control"""
    try:
        # If custom system prompt, model, or headless mode provided, reinitialize agent
        if request.system_prompt or request.model or request.headless != True:
            await agent_manager.reinitialize_agent(
                instructions=request.system_prompt,
                model=request.model,
                headless=request.headless
            )
        
        agent = await agent_manager.get_agent()
        
        # Convert messages to agent format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Limit conversation history to prevent context overflow
        # Keep only the last 10 messages (5 exchanges)
        if len(messages) > 10:
            print(f"⚠️  Truncating conversation history from {len(messages)} to 10 messages")
            messages = messages[-10:]
        
        if request.stream:
            async def generate():
                try:
                    final_response = ""
                    step_count = 0
                    seen_tool_calls = set()
                    
                    # Use stream_mode="values" to get complete state updates
                    async for chunk in agent.astream({"messages": messages}, stream_mode="values"):
                        if "messages" not in chunk or not chunk["messages"]:
                            continue
                        
                        # Get the last message in the conversation
                        last_message = chunk["messages"][-1]
                        msg_type = type(last_message).__name__
                        
                        # Handle AIMessage with tool calls
                        if msg_type == "AIMessage" and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                # Create unique identifier for this tool call
                                tool_call_id = f"{tool_call.get('name', 'unknown')}_{tool_call.get('id', '')}"
                                
                                # Skip if we've already seen this tool call
                                if tool_call_id in seen_tool_calls:
                                    continue
                                seen_tool_calls.add(tool_call_id)
                                
                                step_count += 1
                                tool_name = tool_call.get('name', 'unknown')
                                tool_args = tool_call.get('args', {})
                                
                                # Log tool call to console
                                print(f"\n{'='*60}")
                                print(f"[AGENT THINKING] Step {step_count}: Calling tool")
                                print(f"Tool: {tool_name}")
                                print(f"Args: {json.dumps(tool_args, indent=2)}")
                                print(f"{'='*60}\n")
                                
                                # Stream thinking message to client
                                yield f"data: {json.dumps({'type': 'thinking', 'content': f'Calling {tool_name}...'})}\n\n"
                        
                        # Handle AIMessage with content (final response)
                        elif msg_type == "AIMessage" and hasattr(last_message, 'content') and last_message.content:
                            content = str(last_message.content).strip()
                            
                            # Only update if content has changed
                            if content and content != final_response:
                                final_response = content
                                # Stream the complete content (not incremental)
                                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    
                    # Send final event and log complete output
                    if final_response:
                        print(f"\n{'='*60}")
                        print(f"[AGENT OUTPUT]")
                        print(final_response)
                        print(f"{'='*60}\n")
                        
                        yield f"data: {json.dumps({'type': 'final', 'content': final_response})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'final', 'content': 'Task completed.'})}\n\n"
                    
                except Exception as e:
                    import traceback
                    error_detail = f"{str(e)}\n{traceback.format_exc()}"
                    print(f"Error in generate: {error_detail}")
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            result = await agent.ainvoke({"messages": messages})
            return {
                "response": result["messages"][-1].content,
                "done": True
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/structured")
async def structured_chat(request: StructuredChatRequest):
    """Chat endpoint with structured output support (JSON schema) and browser headless control"""
    try:
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        
        # If custom system prompt, model, or headless mode provided, reinitialize agent
        if request.system_prompt or request.model or request.headless != True:
            await agent_manager.reinitialize_agent(
                instructions=request.system_prompt,
                model=request.model,
                headless=request.headless
            )
        
        agent = await agent_manager.get_agent()
        
        # Convert messages to agent format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Limit conversation history
        if len(messages) > 10:
            print(f"⚠️  Truncating conversation history from {len(messages)} to 10 messages")
            messages = messages[-10:]
        
        # Add structured output instruction to the last user message
        schema_str = json.dumps(request.structured_output_format, indent=2)
        structured_instruction = f"\n\nIMPORTANT: You MUST respond with valid JSON matching this exact schema:\n{schema_str}\n\nDo not include any text outside the JSON object."
        
        # Append instruction to last message
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += structured_instruction
        
        # Get response from agent
        print(f"\n{'='*60}")
        print(f"[STRUCTURED OUTPUT REQUEST]")
        print(f"Schema: {json.dumps(request.structured_output_format, indent=2)}")
        print(f"Browser mode: {'headless' if request.headless else 'visible'}")
        print(f"{'='*60}\n")
        
        result = await agent.ainvoke({"messages": messages})
        response_content = result["messages"][-1].content
        
        # Try to parse as JSON
        try:
            # Extract JSON from response (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                structured_data = json.loads(json_str)
            else:
                structured_data = json.loads(response_content)
            
            print(f"\n{'='*60}")
            print(f"[STRUCTURED OUTPUT]")
            print(json.dumps(structured_data, indent=2))
            print(f"{'='*60}\n")
            
            return {
                "data": structured_data,
                "raw_response": response_content,
                "success": True
            }
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON: {e}")
            return {
                "data": None,
                "raw_response": response_content,
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}"
            }
    
    except Exception as e:
        import traceback
        print(f"Error in structured_chat: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        agent = await agent_manager.get_agent()
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            messages = data.get("messages", [])
            
            # Stream response
            async for chunk in agent.astream({"messages": messages}, stream_mode="values"):
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
            instructions=request.instructions,
            headless=request.headless
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
║  ✓ Headless browser control (API parameter)                ║
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