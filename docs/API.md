# API Reference

## Endpoints

### POST /api/chat

Chat with the agent (streaming or non-streaming).

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Your question"}
  ],
  "stream": true,
  "model": "anthropic:claude-sonnet-4-20250514",
  "system_prompt": "Custom instructions",
  "enable_research": true,
  "google_sheets": [
    {"spreadsheet_id": "SHEET_ID"}
  ]
}
```

**Response (streaming):**
```
data: {"content": "Hello", "done": false}
data: {"content": " world", "done": false}
data: {"content": "", "done": true}
```

**Response (non-streaming):**
```json
{
  "response": "Complete response text",
  "done": true
}
```

### WS /ws/chat

WebSocket chat endpoint.

**Send:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

**Receive:**
```json
{"type": "message", "content": "Hello", "done": false}
{"type": "message", "content": " there", "done": false}
{"type": "message", "content": "", "done": true}
```

### GET /api/tools

List all available tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "duckduckgo_search",
      "description": "Search the web",
      "parameters": {...}
    }
  ]
}
```

### GET /api/config

Get current configuration.

**Response:**
```json
{
  "instructions": "System prompt",
  "enable_research": true,
  "model": "anthropic:claude-sonnet-4-20250514"
}
```

### POST /api/config

Update configuration.

**Request:**
```json
{
  "instructions": "New system prompt",
  "enable_research": false
}
```

### GET /api/health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "tools_count": 15
}
```

### GET /oauth2callback

OAuth callback for Google Sheets (internal use).

### GET /api/sheets/status

Check Google Sheets authentication status.

**Response:**
```json
{
  "authenticated": true
}
```

## Models

Supported models:

- `anthropic:claude-sonnet-4-20250514`
- `anthropic:claude-3-5-sonnet-20241022`
- `openai:gpt-4o`
- `openai:gpt-3.5-turbo`
- `google_genai:gemini-2.5-flash`
- `ollama:llama3`

## Examples

### cURL

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Hello'}],
    stream: false
  })
});
const data = await response.json();
console.log(data);
```

## Error Handling

**Error Response:**
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**Common Errors:**
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (missing API key)
- `500` - Server error

## Rate Limits

Depends on your LLM provider:
- Anthropic: Varies by plan
- OpenAI: Varies by plan
- Google: 10 requests/minute (free tier)
- Ollama: No limits (local)
