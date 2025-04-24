import os
import json
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import requests # type: ignore
from docusign_esign import ApiClient # type: ignore

class DocuSignAuth:
    def __init__(self):
        """Initialize DocuSign authentication handler"""
        # Use only environment variables for Render compatibility
        self.auth_server = os.getenv('DOCUSIGN_AUTH_SERVER')
        if not self.auth_server:
            st.warning("DOCUSIGN_AUTH_SERVER environment variable not set.") # Optional warning
            # You might want to raise an Exception here or provide a default if applicable

        self.token_path = os.getenv('TOKEN_PATH', os.path.join('.tokens', 'token.json'))
        self.api_client = ApiClient()
        self.redirect_uri = None  # Will be set dynamically
        
        # Create token directory if it doesn't exist
        token_dir = os.path.dirname(os.path.abspath(self.token_path))
        if token_dir:
            Path(token_dir).mkdir(parents=True, exist_ok=True)

    def _get_credentials(self):
        """Get credentials from session state or fallback to env"""
        # Prioritize session state (if user entered manually) then environment variables
        client_id = getattr(st.session_state, 'client_id', None) or os.getenv('DOCUSIGN_CLIENT_ID')
        client_secret = getattr(st.session_state, 'client_secret', None) or os.getenv('DOCUSIGN_CLIENT_SECRET')
        account_id = getattr(st.session_state, 'account_id', None) or os.getenv('DOCUSIGN_ACCOUNT_ID') # Added fallback for account_id
        
        # Add checks/warnings if critical env vars are missing
        if not client_id:
            st.warning("DOCUSIGN_CLIENT_ID environment variable not set.")
        if not client_secret:
            st.warning("DOCUSIGN_CLIENT_SECRET environment variable not set.")

        return client_id, client_secret, account_id

    def get_consent_url(self, redirect_uri=None):
        """Generate the consent URL for DocuSign OAuth"""
        client_id, _, _ = self._get_credentials()
        if not client_id:
            raise Exception("DocuSign Integration Key (Client ID) is required")
            
        # Use environment variable for the default redirect URI
        self.redirect_uri = redirect_uri or os.getenv('DOCUSIGN_REDIRECT_URI', 'http://localhost:8501')
        
        if not self.auth_server:
             raise Exception("DocuSign Auth Server Hostname is not configured (DOCUSIGN_AUTH_SERVER env var missing)")
        
        return (
            f"https://{self.auth_server}/oauth/auth"
            f"?response_type=code"
            f"&scope=signature%20impersonation%20spring_write%20spring_read"
            f"&client_id={client_id}"
            f"&redirect_uri={self.redirect_uri}"
        )

    def get_token_from_code(self, code, redirect_uri=None):
        """Exchange authorization code for access token"""
        client_id, client_secret, _ = self._get_credentials()
        if not client_id or not client_secret:
            raise Exception("DocuSign Integration Key (Client ID) and Secret Key are required")
            
        url = f"https://{self.auth_server}/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri or self.redirect_uri
        }
        print(f"DEBUG [get_token_from_code]: URI='{data['redirect_uri']}', ClientID='{client_id}'")
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self._save_token(token_data)
            return token_data
        else:
            raise Exception(f"Failed to get token: {response.text}")

    def refresh_token(self, refresh_token):
        """Refresh the access token using refresh token"""
        client_id, client_secret, _ = self._get_credentials()
        if not client_id or not client_secret:
            raise Exception("DocuSign Integration Key (Client ID) and Secret Key are required")
            
        url = f"https://{self.auth_server}/oauth/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self._save_token(token_data)
            return token_data
        else:
            raise Exception(f"Failed to refresh token: {response.text}")

    def _save_token(self, token_data):
        """Save token data to file"""
        token_data['timestamp'] = datetime.now().isoformat()
        with open(self.token_path, 'w') as f:
            json.dump(token_data, f)

    def load_token(self):
        """Load token data from file"""
        try:
            with open(self.token_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def is_token_valid(self, token_data):
        """Check if the current token is valid"""
        if not token_data:
            return False
        
        timestamp = datetime.fromisoformat(token_data['timestamp'])
        expires_in = token_data['expires_in']
        expiration_time = timestamp + timedelta(seconds=expires_in)
        
        # Consider token invalid if it expires in less than 5 minutes
        return datetime.now() < (expiration_time - timedelta(minutes=5))

    def delete_token(self):
        """Delete the stored token file"""
        try:
            if os.path.exists(self.token_path):
                os.remove(self.token_path)
                return True
        except Exception:
            pass
        return False
