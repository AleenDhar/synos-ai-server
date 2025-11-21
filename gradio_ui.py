"""Gradio UI for DeepAgent with Google Sheets Integration

Provides a web interface for:
- Chatting with the AI agent
- Managing Google Sheets OAuth connection
- Testing Google Sheets search functionality
"""

import gradio as gr
import requests
import json
from google_sheets_auth import GoogleSheetsAuth

# Initialize
sheets_auth = GoogleSheetsAuth()
SERVER_URL = "http://localhost:8000"


def check_auth_status():
    """Check if Google Sheets is authenticated"""
    if sheets_auth.is_authenticated():
        return "✅ Connected to Google Sheets"
    return "❌ Not connected to Google Sheets"


def get_auth_link():
    """Generate OAuth authorization link and open it"""
    try:
        auth_url = sheets_auth.get_auth_url()
        # Return the URL so it can be opened
        return auth_url
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def disconnect_sheets():
    """Disconnect Google Sheets"""
    try:
        sheets_auth.revoke_credentials()
        return "✅ Disconnected from Google Sheets"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def chat_with_agent(message, history):
    """Send message to agent and get response"""
    try:
        # Build messages from history
        messages = []
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": message})
        
        # Send to server
        response = requests.post(
            f"{SERVER_URL}/api/chat",
            json={"messages": messages, "stream": False},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response")
        else:
            return f"❌ Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.Timeout:
        return "❌ Request timed out. The agent might be processing a complex task."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def test_sheets_search(spreadsheet_id, keywords, sheet_name):
    """Test Google Sheets search directly"""
    try:
        if not sheets_auth.is_authenticated():
            return "❌ Please connect to Google Sheets first"
        
        # Call the tool directly
        from custom_tools.google_sheets_tools import find_in_google_sheet
        
        result = find_in_google_sheet.invoke({
            "spreadsheet_id": spreadsheet_id,
            "keywords": keywords,
            "sheet_name": sheet_name if sheet_name else None
        })
        
        return result
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Create Gradio Interface
with gr.Blocks(title="DeepAgent with Google Sheets", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 DeepAgent Server with Google Sheets
    
    AI Agent with web search, research capabilities, and Google Sheets integration.
    """)
    
    with gr.Tabs():
        # Chat Tab
        with gr.Tab("💬 Chat"):
            gr.Markdown("### Chat with AI Agent")
            
            auth_status_chat = gr.Textbox(
                label="Google Sheets Status",
                value=check_auth_status(),
                interactive=False
            )
            
            refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
            refresh_status_btn.click(
                check_auth_status,
                outputs=[auth_status_chat]
            )
            
            chatbot = gr.Chatbot(
                label="Agent Chat",
                height=500,
                show_copy_button=True
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Message",
                    placeholder="Ask me anything! Try: 'Search my Google Sheet for sales data'",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            gr.Markdown("""
            **Example queries:**
            - "Find all rows with 'john' in my Google Sheet: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            - "Search for 'sales' in sheet ID: YOUR_SHEET_ID"
            - "List all sheets in spreadsheet: YOUR_SHEET_ID"
            """)
            
            def respond(message, chat_history):
                bot_message = chat_with_agent(message, chat_history)
                chat_history.append((message, bot_message))
                return "", chat_history
            
            send_btn.click(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
            msg.submit(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
        
        # Google Sheets Setup Tab
        with gr.Tab("🔐 Google Sheets Setup"):
            gr.Markdown("""
            ### Connect Google Sheets
            
            **Setup Steps:**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing one
            3. Enable Google Sheets API
            4. Create OAuth 2.0 credentials (Desktop app)
            5. Download credentials as `client_secrets.json` in project root
            6. Click "Connect Google Sheets" below
            """)
            
            auth_status_setup = gr.Textbox(
                label="Connection Status",
                value=check_auth_status(),
                interactive=False
            )
            
            with gr.Row():
                connect_btn = gr.Button("🔗 Connect Google Sheets", variant="primary")
                disconnect_btn = gr.Button("🔌 Disconnect", variant="stop")
            
            gr.Markdown("""
            **Instructions:**
            1. Click "Connect Google Sheets" button above
            2. A new tab will open with Google's authorization page
            3. Sign in and grant permissions
            4. You'll be redirected back automatically
            5. Refresh the status to confirm connection
            """)
            
            # Hidden textbox to store the auth URL
            auth_url_box = gr.Textbox(visible=False)
            
            # JavaScript to open URL in new tab
            connect_btn.click(
                get_auth_link,
                outputs=[auth_url_box]
            ).then(
                None,
                inputs=[auth_url_box],
                outputs=None,
                js="(url) => { if(url && !url.startsWith('Error')) { window.open(url, '_blank'); } else { alert(url); } }"
            )
            
            disconnect_btn.click(
                disconnect_sheets,
                outputs=[auth_status_setup]
            ).then(
                check_auth_status,
                outputs=[auth_status_chat]
            )
            
            gr.Markdown("""
            **Troubleshooting:**
            - If the popup is blocked, allow popups for this site
            - Make sure `client_secrets.json` exists in project root
            - Check that Google Sheets API is enabled in Google Cloud Console
            """)
        
        # Test Tab
        with gr.Tab("🧪 Test Google Sheets"):
            gr.Markdown("### Test Google Sheets Search")
            
            auth_status_test = gr.Textbox(
                label="Connection Status",
                value=check_auth_status(),
                interactive=False
            )
            
            with gr.Row():
                spreadsheet_id_input = gr.Textbox(
                    label="Spreadsheet ID",
                    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    info="Get this from the Google Sheets URL after /d/"
                )
            
            with gr.Row():
                keywords_input = gr.Textbox(
                    label="Keywords",
                    placeholder="john sales",
                    info="Space-separated keywords to search for"
                )
                sheet_name_input = gr.Textbox(
                    label="Sheet Name (Optional)",
                    placeholder="Sheet1",
                    info="Leave empty to search all sheets"
                )
            
            test_btn = gr.Button("🔍 Search", variant="primary")
            
            test_output = gr.Textbox(
                label="Search Results",
                lines=15,
                interactive=False
            )
            
            test_btn.click(
                test_sheets_search,
                inputs=[spreadsheet_id_input, keywords_input, sheet_name_input],
                outputs=[test_output]
            )
            
            gr.Markdown("""
            **How to get Spreadsheet ID:**
            - Open your Google Sheet
            - Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
            - Copy the `SPREADSHEET_ID` part
            """)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║              DeepAgent Gradio UI with Google Sheets          ║
╠══════════════════════════════════════════════════════════════╣
║  Make sure the FastAPI server is running on port 8000       ║
║  Starting Gradio UI on: http://localhost:7860               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
