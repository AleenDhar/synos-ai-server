#!/usr/bin/env python3
"""Test the API with a simple request first"""

import requests
import json

# Simple test without Google Sheets
print("Testing simple request...")
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "messages": [
            {"role": "user", "content": "What is procurement in 2 sentences?"}
        ],
        "stream": False,
        "model": "openai:gpt-4"
    },
    timeout=60
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Simple request works!")
    print(f"Response: {response.json()['response'][:200]}...")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "="*60 + "\n")

# Test with Google Sheets
print("Testing with Google Sheets...")
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "messages": [
            {"role": "user", "content": "Search for 'intake' in the sheets"}
        ],
        "google_sheets": [
            {
                "spreadsheet_id": "19mw4foLPQq5SWsdFTwQpDa6-pOiOXT7HT9n_a0BOfHA",
                "sheet_name": "solution"
            }
        ],
        "stream": False,
        "model": "openai:gpt-4"
    },
    timeout=120
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Google Sheets request works!")
    print(f"Response: {response.json()['response'][:200]}...")
else:
    print(f"❌ Error: {response.text}")
