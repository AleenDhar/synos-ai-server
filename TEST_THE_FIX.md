# How to Test the Streaming Loop Fix

## Quick Test

1. **Start the server:**
   ```bash
   python3 server.py
   ```

2. **Open the web UI:**
   ```
   http://localhost:8000
   ```

3. **Test with a Salesforce query that returns large data:**
   ```
   Get details for Opportunity 006P700000O0NMzIAN
   ```

4. **Expected behavior:**
   - ✅ Agent calls the MCP tool once
   - ✅ Receives truncated but usable data
   - ✅ Analyzes the data immediately
   - ✅ Provides answer to user
   - ✅ No loops, no file read errors
   - ✅ Smooth streaming experience

5. **What you should NOT see:**
   - ❌ "[SAVED TO FILE: ...]" messages
   - ❌ "Error: File not found" messages
   - ❌ Same tool being called repeatedly
   - ❌ Agent stuck in thinking loop

## Verify the Fix

### Check the logs:
```bash
tail -f server.log
```

You should see:
```
[BACKGROUND] Saved large get_record response (38694 chars) to mcp_output/get_record_20251109_203525.json
```

Note: The "[BACKGROUND]" prefix means it's logged but NOT sent to the agent.

### Check saved files:
```bash
ls -lh mcp_output/
```

You should see files being created (for debugging), but the agent doesn't try to read them.

## Test Different Scenarios

### 1. Small Response (< 10KB)
```
Query: Get current time
Expected: Full response returned, no truncation
```

### 2. Large Dict Response (> 10KB)
```
Query: Describe the Account_Planning_Document__c object
Expected: First 20 fields returned, rest truncated
```

### 3. Large List Response (> 10KB)
```
Query: Query all Opportunities
Expected: First 5 records returned, rest truncated
```

### 4. Multiple Queries in Sequence
```
Query 1: Get Opportunity details
Query 2: Get Account details
Query 3: Query related records
Expected: Each query works independently, no loops
```

## Performance Metrics

Track these metrics to verify the fix:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Response Time | < 5 seconds | Time from query to answer |
| API Calls | 1 per query | Check MCP server logs |
| Loop Detection | 0 loops | No repeated tool calls |
| Streaming | Smooth | No interruptions |

## Debugging

If you still see loops:

1. **Check the wrapper code:**
   ```bash
   grep -A 20 "def wrap_mcp_tool" server.py
   ```
   Should NOT contain "SAVED TO FILE" in the return statement.

2. **Check the system prompt:**
   ```bash
   grep -A 10 "HANDLING LARGE" server.py
   ```
   Should NOT mention reading files.

3. **Check for old cached agent:**
   ```bash
   rm -rf __pycache__
   python3 server.py
   ```

4. **Enable debug mode:**
   In server.py, the agent is created with `debug=True`, so you'll see all tool calls.

## Success Criteria

✅ **Fix is working if:**
- Agent responds to queries without loops
- Large responses are handled gracefully
- Streaming works smoothly
- No file read errors
- Response time is reasonable (< 5 seconds)

❌ **Fix needs adjustment if:**
- Agent still tries to read files
- Same tool called multiple times
- "File not found" errors appear
- Agent gets stuck in thinking loop

## Rollback (if needed)

If the fix causes issues, you can rollback:

```bash
git diff server.py  # See what changed
git checkout server.py  # Restore old version
```

But the fix should work! The logic is sound:
- Don't tell agent about files
- Give agent usable truncated data
- Agent works with what it has
- No loops!
