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
        # If we have client_id in session state, use both values from session state
        if hasattr(st.session_state, 'client_id') and st.session_state.client_id:
            client_id = st.session_state.client_id
            client_secret = st.session_state.client_secret
        else:
            # Only use environment variables if no session state exists
            client_id = os.getenv('DOCUSIGN_CLIENT_ID')
            client_secret = os.getenv('DOCUSIGN_CLIENT_SECRET')
        
        account_id = getattr(st.session_state, 'account_id', None) or os.getenv('DOCUSIGN_ACCOUNT_ID')
        
        # Add checks/warnings
        if not client_id:
            st.warning("DocuSign Client ID not available.")
        if not client_secret:
            st.warning("DocuSign Client Secret not available.")

        return client_id, client_secret, account_id

    def get_consent_url(self, redirect_uri=None):
        """Generate the consent URL for DocuSign OAuth"""
        client_id, client_secret, _ = self._get_credentials()
        if not client_id:
            raise Exception("DocuSign Integration Key (Client ID) is required")
            
        # Store credentials to a temporary file to survive redirect
        self._store_temp_credentials(client_id, client_secret)
        
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
        # Try to get credentials from session state first
        client_id, client_secret, _ = self._get_credentials()
        
        # If credentials not available from session state, try the temp file
        if not client_id or not client_secret:
            print("DEBUG [get_token_from_code]: Credentials not found in session, trying temp file")
            client_id, client_secret = self._load_temp_credentials()
            
        if not client_id or not client_secret:
            raise Exception("DocuSign Integration Key (Client ID) and Secret Key are required")
            
        print(f"DEBUG [get_token_from_code]: Got credentials: client_id={client_id[:8]}...")
            
        url = f"https://{self.auth_server}/oauth/token"
        
        # IMPORTANT: Force the redirect URI to be the Render URL consistently
        consistent_redirect_uri = "https://clm-api-examples.onrender.com/"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': consistent_redirect_uri  # Use consistent URL instead of dynamic one
        }
        
        print(f"DEBUG [get_token_from_code]: URI='{data['redirect_uri']}', ClientID='{client_id}'")
        response = requests.post(url, data=data)
        
        print(f"DEBUG [get_token_from_code-RESPONSE]: Status={response.status_code}, Headers={response.headers}")
        
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

    def _store_temp_credentials(self, client_id, client_secret):
        """Store credentials temporarily to survive the redirect flow"""
        try:
            temp_creds = {
                "client_id": client_id,
                "client_secret": client_secret,
                "timestamp": datetime.now().isoformat()
            }
            
            # Create a temporary credentials file
            temp_creds_path = os.path.join('.tokens', 'temp_creds.json')
            os.makedirs(os.path.dirname(temp_creds_path), exist_ok=True)
            
            with open(temp_creds_path, 'w') as f:
                json.dump(temp_creds, f)
            
            print(f"DEBUG [_store_temp_credentials]: Stored credentials to temp file")
        except Exception as e:
            print(f"DEBUG [_store_temp_credentials ERROR]: {str(e)}")

    def _load_temp_credentials(self):
        """Load temporary credentials if they exist"""
        try:
            temp_creds_path = os.path.join('.tokens', 'temp_creds.json')
            if os.path.exists(temp_creds_path):
                with open(temp_creds_path, 'r') as f:
                    temp_creds = json.load(f)
                
                # Check if credentials are recent (within last 10 minutes)
                timestamp = datetime.fromisoformat(temp_creds['timestamp'])
                if datetime.now() - timestamp < timedelta(minutes=10):
                    print(f"DEBUG [_load_temp_credentials]: Loaded recent credentials")
                    return temp_creds["client_id"], temp_creds["client_secret"]
                else:
                    print(f"DEBUG [_load_temp_credentials]: Found expired credentials, not using")
        except Exception as e:
            print(f"DEBUG [_load_temp_credentials ERROR]: {str(e)}")
        
        return None, None
