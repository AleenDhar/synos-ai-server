# Next.js Integration Guide - Streaming MCP Server Responses

This guide shows how to integrate the DeepAgent MCP server with a Next.js application using streaming responses.

## Prerequisites

- Next.js 13+ (App Router)
- DeepAgent server running on `http://localhost:8000`

## Installation

```bash
npm install
# or
yarn install
```

## Backend Setup (Next.js API Route)

### 1. Create API Route Handler

Create `app/api/chat/route.ts`:

```typescript
import { NextRequest } from 'next/server';

export const runtime = 'edge'; // Optional: Use edge runtime for better streaming

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    // Call your DeepAgent server
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(JSON.stringify({ error: 'Failed to process request' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
```

## Frontend Setup (React Component)

### 2. Create Chat Component

Create `components/Chat.tsx`:

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      // Add empty assistant message that we'll update
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                console.error('Stream error:', data.error);
                break;
              }

              if (data.content) {
                accumulatedContent += data.content;
                
                // Update the last message with accumulated content
                setMessages((prev) => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: accumulatedContent,
                  };
                  return newMessages;
                });
              }

              if (data.done) {
                break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, an error occurred.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg ${
              message.role === 'user'
                ? 'bg-blue-100 ml-auto max-w-[80%]'
                : 'bg-gray-100 mr-auto max-w-[80%]'
            }`}
          >
            <div className="font-semibold mb-1">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}
        {isLoading && (
          <div className="bg-gray-100 p-4 rounded-lg mr-auto max-w-[80%]">
            <div className="flex items-center space-x-2">
              <div className="animate-pulse">Thinking...</div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
```

### 3. Create Page

Create `app/page.tsx`:

```typescript
import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold text-center py-6">
          DeepAgent Chat
        </h1>
        <Chat />
      </div>
    </main>
  );
}
```

## Alternative: Using WebSocket

For better performance with long conversations, use WebSocket:

### WebSocket API Route

Create `app/api/chat-ws/route.ts`:

```typescript
import { NextRequest } from 'next/server';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  
  // Upgrade to WebSocket
  const upgradeHeader = req.headers.get('upgrade');
  
  if (upgradeHeader !== 'websocket') {
    return new Response('Expected WebSocket', { status: 426 });
  }

  // Proxy to DeepAgent WebSocket
  const ws = new WebSocket('ws://localhost:8000/ws/chat');
  
  return new Response(null, {
    status: 101,
    headers: {
      'Upgrade': 'websocket',
      'Connection': 'Upgrade',
    },
  });
}
```

### WebSocket Hook

Create `hooks/useWebSocketChat.ts`:

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function useWebSocketChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/chat');

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        if (data.content) {
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content += data.content;
            } else {
              newMessages.push({ role: 'assistant', content: data.content });
            }
            
            return newMessages;
          });
        }
        
        if (data.done) {
          setIsLoading(false);
        }
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.content);
        setIsLoading(false);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || !isConnected) return;

    const userMessage: Message = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    wsRef.current.send(
      JSON.stringify({
        messages: [...messages, userMessage],
      })
    );
  }, [isConnected, messages]);

  return {
    messages,
    isConnected,
    isLoading,
    sendMessage,
  };
}
```

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Styling with Tailwind CSS

Install Tailwind CSS:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Configure `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

## Running the Application

1. Start the DeepAgent server:
```bash
./start.sh
```

2. Start the Next.js app:
```bash
npm run dev
```

3. Open `http://localhost:3000`

## Advanced Features

### Add Markdown Support

```bash
npm install react-markdown
```

Update the message rendering:

```typescript
import ReactMarkdown from 'react-markdown';

// In your message component:
<ReactMarkdown>{message.content}</ReactMarkdown>
```

### Add Code Syntax Highlighting

```bash
npm install react-syntax-highlighter @types/react-syntax-highlighter
```

### Add Loading States

```typescript
{isLoading && (
  <div className="flex items-center space-x-2">
    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-100" />
    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-200" />
  </div>
)}
```

## Error Handling

Add proper error boundaries and retry logic:

```typescript
const [error, setError] = useState<string | null>(null);

// In your fetch:
try {
  // ... fetch logic
} catch (error) {
  setError('Failed to connect to the server. Please try again.');
  setMessages((prev) => [
    ...prev,
    { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
  ]);
}
```

## Production Deployment

### Update API URL

In production, update the API URL in your environment variables:

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://your-deepagent-server.com
```

### CORS Configuration

Update your DeepAgent server to allow your Next.js domain:

```python
# In server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-nextjs-app.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

**Issue: Streaming not working**
- Ensure your server supports SSE (Server-Sent Events)
- Check browser console for errors
- Verify CORS settings

**Issue: WebSocket connection fails**
- Check if the WebSocket endpoint is accessible
- Verify firewall settings
- Use `wss://` for HTTPS sites

**Issue: Messages not updating**
- Check React state updates
- Verify the SSE data format
- Add console.logs to debug the stream

## Complete Example Repository

For a complete working example, see the `examples/nextjs` directory in the DeepAgent repository.
