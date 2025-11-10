# Model Usage Guide

## Supported Models

The DeepAgent server supports multiple AI models from different providers:

### 1. OpenAI (ChatGPT)
- `openai:gpt-4` - GPT-4 (most capable)
- `openai:gpt-4-turbo` - GPT-4 Turbo (faster, cheaper)
- `openai:gpt-3.5-turbo` - GPT-3.5 Turbo (fastest, cheapest)

### 2. Anthropic (Claude)
- `anthropic:claude-sonnet-4-20250514` - Claude Sonnet 4 (latest)
- `anthropic:claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `anthropic:claude-3-opus-20240229` - Claude 3 Opus (most capable)

### 3. Google (Gemini)
- `google_genai:gemini-2.5-flash` - Gemini 2.5 Flash (fast, efficient)
- `google_genai:gemini-2.0-flash-exp` - Gemini 2.0 Flash Experimental
- `google_genai:gemini-pro` - Gemini Pro

### 4. Ollama (Local Models)
- `ollama:llama3` - Llama 3 (local)
- `ollama:mistral` - Mistral (local)
- `ollama:codellama` - Code Llama (local)

## Configuration

### Environment Variables

Add your API keys to `.env`:

```env
# Default model
MODEL=google_genai:gemini-2.5-flash

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
GOOGLE_API_KEY=AIzaSyxxxxx
```

## Usage Examples

### 1. Use Default Model (from .env)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "List all Salesforce opportunities"
    }
  ],
  "stream": true
}
```

### 2. Use ChatGPT (GPT-4)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze this opportunity data"
    }
  ],
  "stream": true,
  "model": "openai:gpt-4"
}
```

### 3. Use Claude Sonnet

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Write a detailed analysis report"
    }
  ],
  "stream": true,
  "model": "anthropic:claude-sonnet-4-20250514"
}
```

### 4. Use GPT-3.5 Turbo (Fast & Cheap)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Quick query: what's the current time?"
    }
  ],
  "stream": true,
  "model": "openai:gpt-3.5-turbo"
}
```

### 5. Use Local Ollama Model

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Help me with this code"
    }
  ],
  "stream": true,
  "model": "ollama:llama3"
}
```

### 6. Combine Model + Custom System Prompt

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze account performance"
    }
  ],
  "stream": true,
  "model": "openai:gpt-4",
  "system_prompt": "You are a business analyst. Provide detailed insights with charts and recommendations."
}
```

## Model Selection Tips

### When to use GPT-4:
- Complex reasoning tasks
- Detailed analysis
- Code generation
- When accuracy is critical

### When to use GPT-3.5 Turbo:
- Simple queries
- Fast responses needed
- Cost optimization
- High volume requests

### When to use Claude:
- Long context understanding
- Document analysis
- Creative writing
- Detailed explanations

### When to use Gemini:
- Fast responses
- Multimodal tasks
- Cost-effective
- Good balance of speed/quality

### When to use Ollama (Local):
- Privacy concerns
- No internet connection
- No API costs
- Full control

## API Endpoint

**POST** `http://localhost:8000/api/chat`

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Your question"}
  ],
  "stream": true,
  "model": "openai:gpt-4",  // Optional: override default model
  "system_prompt": "Custom instructions",  // Optional
  "enable_research": false  // Optional: enable deep research
}
```

**Response:** Server-Sent Events (SSE) stream

## Testing in Postman

1. Create POST request to `http://localhost:8000/api/chat`
2. Set header: `Content-Type: application/json`
3. Set body with your desired model
4. Send and watch the streaming response

## Cost Comparison (Approximate)

| Model | Speed | Cost | Quality |
|-------|-------|------|---------|
| GPT-4 | Slow | $$$$ | Excellent |
| GPT-4 Turbo | Medium | $$$ | Excellent |
| GPT-3.5 Turbo | Fast | $ | Good |
| Claude Sonnet | Medium | $$$ | Excellent |
| Gemini Flash | Fast | $$ | Very Good |
| Ollama (Local) | Medium | Free | Good |

## Notes

- Model selection is per-request, so you can mix models in different requests
- The agent will be reinitialized when you change models
- All models have access to the same tools (MCP, Salesforce, etc.)
- Streaming works with all models
