# Structured Output Guide

## Overview

The `/api/chat/structured` endpoint allows you to get responses in a specific JSON format by providing a JSON schema. This is useful for:
- Extracting specific data fields
- Getting consistent response formats
- Building integrations that need predictable output
- Data analysis and reporting

## Endpoint

**POST** `http://localhost:8000/api/chat/structured`

## Request Format

```json
{
  "messages": [
    {"role": "user", "content": "Your question"}
  ],
  "structured_output_format": {
    "field1": "description",
    "field2": "description"
  },
  "system_prompt": "Optional custom instructions",
  "model": "openai:gpt-4",
  "enable_research": false
}
```

## Response Format

```json
{
  "data": {
    // Your structured data matching the schema
  },
  "raw_response": "The complete AI response",
  "success": true
}
```

## Examples

### Example 1: Opportunity Analysis

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze opportunity 006P700000O0NMzIAN and tell me everything about it"
    }
  ],
  "structured_output_format": {
    "opportunity_name": "string",
    "opportunity_id": "string",
    "stage": "string",
    "amount": "number",
    "close_date": "string (YYYY-MM-DD)",
    "account_name": "string",
    "probability": "number (0-100)",
    "key_insights": ["array of strings"],
    "risks": ["array of strings"],
    "next_steps": ["array of strings"]
  },
  "model": "openai:gpt-4",
  "stream": false
}
```

**Response:**
```json
{
  "data": {
    "opportunity_name": "Humain_S2P",
    "opportunity_id": "006P700000O0NMzIAN",
    "stage": "Qualified",
    "amount": 160000,
    "close_date": "2026-04-01",
    "account_name": "Acme Corp",
    "probability": 75,
    "key_insights": [
      "Large deal with strategic account",
      "Strong executive sponsorship",
      "Competitive situation with 2 vendors"
    ],
    "risks": [
      "Budget approval pending",
      "Timeline may slip to Q3"
    ],
    "next_steps": [
      "Schedule executive briefing",
      "Prepare ROI analysis",
      "Submit proposal by end of month"
    ]
  },
  "raw_response": "...",
  "success": true
}
```

### Example 2: Account Summary

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Give me a summary of all open opportunities for account XYZ"
    }
  ],
  "structured_output_format": {
    "account_name": "string",
    "total_opportunities": "number",
    "total_pipeline_value": "number",
    "opportunities": [
      {
        "name": "string",
        "id": "string",
        "stage": "string",
        "amount": "number",
        "close_date": "string"
      }
    ],
    "summary": "string"
  },
  "model": "openai:gpt-4"
}
```

### Example 3: Data Extraction

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Extract key contact information from opportunity 006P700000O0NMzIAN"
    }
  ],
  "structured_output_format": {
    "primary_contact": {
      "name": "string",
      "title": "string",
      "email": "string",
      "phone": "string"
    },
    "decision_makers": [
      {
        "name": "string",
        "title": "string",
        "role": "string"
      }
    ],
    "last_contact_date": "string",
    "next_follow_up": "string"
  },
  "model": "openai:gpt-4"
}
```

### Example 4: Competitive Analysis

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze the competitive landscape for opportunity 006P700000O0NMzIAN"
    }
  ],
  "structured_output_format": {
    "competitors": [
      {
        "name": "string",
        "strengths": ["array of strings"],
        "weaknesses": ["array of strings"],
        "threat_level": "string (High/Medium/Low)"
      }
    ],
    "our_position": {
      "strengths": ["array of strings"],
      "differentiators": ["array of strings"],
      "win_probability": "number (0-100)"
    },
    "strategy": "string"
  },
  "model": "openai:gpt-4"
}
```

### Example 5: Sales Forecast

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Generate a sales forecast for Q1 2026"
    }
  ],
  "structured_output_format": {
    "quarter": "string",
    "total_pipeline": "number",
    "weighted_pipeline": "number",
    "forecast_categories": {
      "commit": "number",
      "best_case": "number",
      "pipeline": "number"
    },
    "top_deals": [
      {
        "name": "string",
        "amount": "number",
        "probability": "number",
        "expected_close": "string"
      }
    ],
    "risks": ["array of strings"],
    "opportunities": ["array of strings"]
  },
  "model": "openai:gpt-4"
}
```

### Example 6: Simple Data Extraction

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the stage and amount of opportunity 006P700000O0NMzIAN?"
    }
  ],
  "structured_output_format": {
    "stage": "string",
    "amount": "number",
    "currency": "string"
  },
  "model": "openai:gpt-3.5-turbo"
}
```

### Example 7: Multi-Record Analysis

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "List all opportunities closing this month"
    }
  ],
  "structured_output_format": {
    "month": "string",
    "total_count": "number",
    "total_value": "number",
    "opportunities": [
      {
        "id": "string",
        "name": "string",
        "amount": "number",
        "close_date": "string",
        "stage": "string",
        "owner": "string"
      }
    ]
  },
  "model": "openai:gpt-4"
}
```

## Schema Guidelines

### Supported Types
- `"string"` - Text values
- `"number"` - Numeric values (int or float)
- `"boolean"` - true/false
- `["array"]` - Arrays of values
- `{"object"}` - Nested objects

### Best Practices

1. **Be Specific:** Describe the expected format
   ```json
   "close_date": "string (YYYY-MM-DD format)"
   ```

2. **Use Arrays for Lists:**
   ```json
   "contacts": [
     {
       "name": "string",
       "email": "string"
     }
   ]
   ```

3. **Nest Related Data:**
   ```json
   "opportunity": {
     "details": {...},
     "contacts": [...],
     "activities": [...]
   }
   ```

4. **Include Descriptions:**
   ```json
   "probability": "number (0-100, percentage chance of closing)"
   ```

## Model Recommendations

### For Structured Output:
- **GPT-4** - Best accuracy and schema adherence
- **GPT-4 Turbo** - Good balance of speed and accuracy
- **GPT-3.5 Turbo** - Fast, good for simple schemas

### Not Recommended:
- Streaming models (use `stream: false`)
- Local models (may not follow schema well)

## Error Handling

### Success Response:
```json
{
  "data": {...},
  "raw_response": "...",
  "success": true
}
```

### Failure Response:
```json
{
  "data": null,
  "raw_response": "The AI's response",
  "success": false,
  "error": "Failed to parse JSON: ..."
}
```

## Tips

1. **Start Simple:** Test with simple schemas first
2. **Validate Output:** Check the `success` field
3. **Use GPT-4:** For complex schemas, use GPT-4
4. **Provide Context:** Give clear instructions in your message
5. **Check Raw Response:** If parsing fails, check `raw_response`

## Postman Testing

1. Create POST request to `http://localhost:8000/api/chat/structured`
2. Set header: `Content-Type: application/json`
3. Use one of the example request bodies above
4. Send and inspect the structured JSON response

## Integration Example

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/structured",
    json={
        "messages": [
            {"role": "user", "content": "Analyze opportunity 006P700000O0NMzIAN"}
        ],
        "structured_output_format": {
            "name": "string",
            "stage": "string",
            "amount": "number"
        },
        "model": "openai:gpt-4"
    }
)

data = response.json()
if data["success"]:
    opp = data["data"]
    print(f"Opportunity: {opp['name']}")
    print(f"Stage: {opp['stage']}")
    print(f"Amount: ${opp['amount']:,.2f}")
else:
    print(f"Error: {data['error']}")
```

## Comparison: Regular vs Structured

### Regular Chat (`/api/chat`)
- Natural language response
- Streaming support
- Flexible format
- Good for conversations

### Structured Chat (`/api/chat/structured`)
- JSON response
- No streaming
- Predictable format
- Good for integrations

Choose based on your use case!
