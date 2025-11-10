# Streaming Loop Fix - Large MCP Response Handling

## Problem
The agent was getting stuck in an infinite loop when using MCP tools with streaming enabled:

1. MCP tool returns large response (>10k chars)
2. Wrapper saves to file: `mcp_output/get_record_20251109_203525.json`
3. Agent receives message: `[SAVED TO FILE: mcp_output/...]` with truncated preview
4. Agent tries to read the file using `read_file()` tool
5. File read fails (path issues or tool not available)
6. Agent retries the same MCP call
7. Loop repeats indefinitely ♾️

## Root Cause
The wrapper was telling the agent about saved files, which triggered the agent's instinct to read them. However:
- The saved files were for debugging/logging only
- The agent's file tools couldn't access them reliably
- The agent didn't need the full data - the preview was sufficient

## Solution
Changed the wrapper to provide **usable truncated data** without mentioning files:

### Before (Caused Loops)
```python
return f"[SAVED TO FILE: {filename}]\n\nTruncated preview:\n{truncated}\n\n[Full data in {filename}]"
```

### After (No Loops)
```python
# For dict: return first 20 keys
summary = {k: v for k, v in list(result.items())[:20]}
truncated = json.dumps(summary, indent=2)[:3000]
return f"{truncated}\n\n... (Response truncated - showing first portion of data. Total size: {len(result_str)} chars)"
```

## Key Changes

### 1. Intelligent Truncation
- **Dict responses**: First 20 keys with full values
- **List responses**: First 5 items
- **String responses**: First 3000 characters

### 2. No File References
- Files are still saved (for debugging)
- But agent is NOT told about them
- Agent works with the truncated data directly

### 3. Updated System Prompt
Removed confusing instructions about reading saved files. New instructions:
- Work with truncated data directly
- Don't try to read files
- Don't retry the same tool call
- The truncation is intelligent and contains key information

## Testing
```bash
python3 test_streaming_fix.py
```

Results:
- ✅ 100KB response truncated to 3KB
- ✅ Agent receives usable JSON data
- ✅ No file references to trigger read attempts
- ✅ Clear indication of truncation

## Benefits
1. **No more infinite loops** - Agent doesn't try to read files
2. **Faster responses** - Agent works with truncated data immediately
3. **Better UX** - Streaming works smoothly without interruptions
4. **Still debuggable** - Full responses saved to `mcp_output/` for inspection

## Usage
Just restart the server - the fix is automatic:
```bash
python3 server.py
```

When MCP tools return large data:
- Agent receives first portion (most important data)
- Agent analyzes and responds immediately
- Full data saved to `mcp_output/` for manual inspection if needed
