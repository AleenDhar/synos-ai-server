# 📊 Google Sheets Integration

Complete OAuth-based Google Sheets integration for your AI agent.

## Features

✅ OAuth 2.0 authentication
✅ Search keywords in sheets
✅ Read specific ranges
✅ List all sheets
✅ Automatic token refresh
✅ Gradio UI for setup

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Google Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Google Sheets API
3. Create OAuth credentials (Desktop app)
4. Download as `client_secrets.json`

### 3. Start Servers

```bash
./start_with_ui.sh
```

Or manually:
```bash
# Terminal 1
python server.py

# Terminal 2
python gradio_ui.py
```

### 4. Connect

1. Open http://localhost:7860
2. Go to "Google Sheets Setup" tab
3. Click "Connect Google Sheets"
4. Follow OAuth flow
5. ✅ Connected!

## Usage

### Get Sheet ID

From URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`

Copy the `SHEET_ID` part.

### Chat Examples

```
"Find 'john' in sheet: YOUR_SHEET_ID"
"Search for 'revenue' in sheet: YOUR_SHEET_ID"
"List all sheets in: YOUR_SHEET_ID"
```

## Available Tools

### find_in_google_sheet
Search for keywords in a sheet.

**Parameters:**
- `spreadsheet_id` (required)
- `keywords` (required)
- `sheet_name` (optional)

### read_google_sheet
Read data from a sheet or range.

**Parameters:**
- `spreadsheet_id` (required)
- `sheet_name` (optional)
- `range_notation` (optional) - e.g., "A1:D10"

### list_google_sheets
List all sheets in a spreadsheet.

**Parameters:**
- `spreadsheet_id` (required)

## Token Storage

Tokens stored in `google_sheets_tokens.json` (auto-created, gitignored).

Auto-refreshes when expired.

## Troubleshooting

**"Client secrets file not found"**
→ Download `client_secrets.json` from Google Cloud Console

**"Not authenticated"**
→ Complete OAuth flow in Gradio UI

**"Spreadsheet not found"**
→ Check Sheet ID and access permissions

**"Invalid grant"**
→ Disconnect and reconnect in Gradio UI

## Security

- OAuth 2.0 standard
- Local token storage
- Read-only access
- Tokens gitignored
- Auto-refresh

## API Usage

```json
{
  "messages": [
    {"role": "user", "content": "Search for 'sales'"}
  ],
  "google_sheets": [
    {"spreadsheet_id": "YOUR_SHEET_ID"}
  ]
}
```

## Files

- `google_sheets_auth.py` - OAuth manager
- `custom_tools/google_sheets_tools.py` - AI tools
- `gradio_ui.py` - Web UI
- `client_secrets.json` - OAuth credentials (download)
- `google_sheets_tokens.json` - Tokens (auto-created)
