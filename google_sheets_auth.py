"""Google Sheets OAuth Authentication Manager

Handles OAuth flow and token management for Google Sheets API access.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = "google_sheets_tokens.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleSheetsAuth:
    """Manage Google Sheets OAuth authentication"""
    
    def __init__(self, client_secrets_file="client_secrets.json"):
        self.client_secrets_file = client_secrets_file
        self.creds = None
        
        # Only load credentials if client_secrets.json exists
        if os.path.exists(self.client_secrets_file):
            self.load_credentials()
        else:
            print(f"⚠️  Google Sheets: {self.client_secrets_file} not found. OAuth disabled.")
    
    def load_credentials(self):
        """Load credentials from token file"""
        if os.path.exists(TOKEN_FILE):
            try:
                self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception as e:
                print(f"⚠️  Failed to load credentials: {e}")
                return
            
            # Refresh if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self.save_credentials()
                except Exception as e:
                    print(f"⚠️  Failed to refresh credentials: {e}")
                    self.creds = None
    
    def save_credentials(self):
        """Save credentials to token file"""
        if self.creds:
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
    
    def get_auth_url(self, redirect_uri='http://localhost:8000/oauth2callback'):
        """Get OAuth authorization URL"""
        if not os.path.exists(self.client_secrets_file):
            return None
        
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
        except Exception as e:
            print(f"⚠️  Failed to generate auth URL: {e}")
            return None
    
    def handle_callback(self, code, redirect_uri='http://localhost:8000/oauth2callback'):
        """Handle OAuth callback and save tokens"""
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        self.creds = flow.credentials
        self.save_credentials()
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.creds is not None and self.creds.valid
    
    def get_service(self):
        """Get Google Sheets service"""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please complete OAuth flow first.")
        return build('sheets', 'v4', credentials=self.creds)
    
    def revoke_credentials(self):
        """Revoke and delete stored credentials"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        self.creds = None
