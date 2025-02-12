import streamlit as st
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from docusign_auth import DocuSignAuth
import webbrowser
import json
import requests

# Get configuration from Streamlit secrets or environment variables
def get_config(key):
    return st.secrets.get(key, os.getenv(key))

# Configure logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_filename = os.path.join(log_directory, f"api_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def serialize_for_logging(obj):
    """Convert objects to JSON-serializable format"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_logging(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_for_logging(v) for k, v in obj.items()}
    return str(obj)

# Initialize DocuSign authentication
auth_handler = DocuSignAuth()

def log_api_call(method, endpoint, request_data=None, response_data=None, error=None):
    """Log API call details"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "request": serialize_for_logging(request_data) if request_data else None,
            "response": serialize_for_logging(response_data) if response_data else None,
            "error": str(error) if error else None
        }
        logger.info(f"API Call: {json.dumps(log_entry, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to log API call: {str(e)}")

def handle_callback():
    """Handle the OAuth callback"""
    if 'code' in st.query_params:
        code = st.query_params['code']
        try:
            redirect_uri = get_actual_redirect_uri()
            token_data = auth_handler.get_token_from_code(code, redirect_uri)
            st.session_state.token_data = token_data
            st.session_state.authenticated = True
            st.success("Successfully authenticated with DocuSign!")
            logger.info("Successfully authenticated with DocuSign")
            # Clear query parameters
            st.query_params.clear()
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)

def check_token():
    """Check and refresh token if necessary"""
    if 'token_data' in st.session_state:
        token_data = st.session_state.token_data
        if not auth_handler.is_token_valid(token_data):
            try:
                new_token_data = auth_handler.refresh_token(token_data['refresh_token'])
                st.session_state.token_data = new_token_data
                logger.info("Token refreshed successfully")
            except Exception as e:
                error_msg = f"Token refresh failed: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
                st.session_state.authenticated = False
                return False
        return True
    return False

def get_docgen_configurations(account_id):
    """Get list of docgen configurations with pagination support"""
    try:
        headers = {
            'Authorization': f"Bearer {st.session_state.token_data['access_token']}",
            'Content-Type': 'application/json'
        }

        all_items = []
        next_url = f"https://apiuatna11.springcm.com/v2/{account_id}/doclauncherconfigurations?limit=100"

        while next_url:
            log_api_call("GET", next_url)
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            log_api_call("GET", next_url, response_data=response_data)
            
            if 'Items' in response_data:
                all_items.extend(response_data['Items'])
            
            # Check if there are more pages
            next_url = response_data.get('Next')
            if next_url:
                st.write(f"Fetching more configurations... ({len(all_items)} so far)")

        # Create final response with all items
        final_response = {
            'Items': all_items,
            'Total': len(all_items)
        }
        
        # Debug logging
        st.write(f"Total configurations found: {len(all_items)}")
        
        return final_response

    except Exception as e:
        error_msg = f"Failed to get docgen configurations: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

def create_doc_launcher_task(account_id, config_href, xml_payload):
    """Create a DocLauncher task using CLM API"""
    try:
        # Prepare the request data
        data = {
            "Data": xml_payload,
            "DataType": "XML",
            "DocLauncherConfiguration": {
                "Href": config_href
            }
        }

        # Prepare headers
        headers = {
            'Authorization': f"Bearer {st.session_state.token_data['access_token']}",
            'Content-Type': 'application/json'
        }

        # Make the API call
        endpoint = f"https://apiuatna11.springcm.com/v2/{account_id}/doclaunchertasks"
        
        # Debug logging
        st.write("API Request:")
        st.json({
            "endpoint": endpoint,
            "data": data
        })
        
        log_api_call("POST", endpoint, request_data=data)

        response = requests.post(
            endpoint,
            headers=headers,
            json=data
        )
        
        # Debug logging
        st.write("API Response Status:", response.status_code)
        
        
        try:
            response_data = response.json()
            st.write("API Response JSON:", response_data)
            if response.status_code not in [200, 202]:
                error_details = response_data.get('Message', response.text)
                logger.error(f"API Error: {response.status_code} - {error_details}")
                st.error(f"API Error ({response.status_code}): {error_details}")
                return None
        except ValueError:
            error_msg = f"API Error ({response.status_code}): {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return None
            
        response.raise_for_status()
        log_api_call("POST", endpoint, response_data=response_data)
        st.success("DocLauncher task created successfully!")
        logger.info(f"DocLauncher task created successfully: {response_data}")
        
        # Display the response
        with st.expander("View Full Response"):
            st.json(response_data)
            
        # Display the DocLauncher Result URL
            # Display DocLauncher Result URL with authentication
            if "DocLauncherResultUrl" in response_data:
                result_url = response_data['DocLauncherResultUrl']
                
                
                # Get the actual content URL with server-side request
                try:
                    headers = {
                        'Authorization': f"Bearer {st.session_state.token_data['access_token']}",
                        'Accept': 'text/html'
                    }
                    response = requests.get(result_url, headers=headers, allow_redirects=True)
                    if response.status_code == 200:
                        st.info("DocLauncher is ready. Click below to open:")
                        st.markdown(f"[Open DocLauncher]({response.url})")
                    else:
                        st.error(f"Failed to get DocLauncher URL: {response.status_code}")
                except Exception as e:
                    st.error(f"Error accessing DocLauncher: {str(e)}")
            
        # Display Status
            if "Status" in response_data:
                status = response_data['Status']
                if status == "Success":
                    st.success(f"Status: {status}")
                else:
                    st.warning(f"Status: {status}")    

        return response_data

    except Exception as e:
        error_msg = f"Failed to create DocLauncher task: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

def get_actual_redirect_uri():
    """Get the actual redirect URI based on how the app is being accessed"""
    # Get the URL where the app is being accessed
    base_url = st.query_params.get('base_url', None)
    if not base_url:
        # Default to secrets/environment variable if no base_url provided
        return get_config('DOCUSIGN_REDIRECT_URI')
    return base_url

def main():
    
    st.image("https://cf-images.us-east-1.prod.boltdns.net/v1/static/6118377982001/f500d879-d469-4a49-851c-0337de041880/7c4ad13a-f83b-4e57-8cbc-7997519f8c96/1280x720/match/image.jpg?v=20250205.7")
    st.title("DocuSign CLM Integration")
    st.write("Enter details below to pull and kick off a Doc Gen Form")

    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'configs' not in st.session_state:
        st.session_state.configs = None
    if 'selected_config' not in st.session_state:
        st.session_state.selected_config = None
    
    # Store the current URL as base_url if not present
  
    

    # Check for callback
    if not st.session_state.authenticated:
        if 'code' in st.query_params:
            handle_callback()

    # Load existing token
    if not st.session_state.authenticated:
        token_data = auth_handler.load_token()
        if token_data and auth_handler.is_token_valid(token_data):
            st.session_state.token_data = token_data
            st.session_state.authenticated = True
            logger.info("Loaded existing valid token")

    # Main application logic
    if not st.session_state.authenticated:
        st.warning("Not authenticated with DocuSign")
        if st.button("Connect to DocuSign"):
            redirect_uri = get_actual_redirect_uri()
            consent_url = auth_handler.get_consent_url(redirect_uri)
            logger.info("Generated DocuSign consent URL")
            st.info("Please copy and open this URL in your browser to authenticate:")
            st.code(consent_url)
            st.info("After authentication, DocuSign will redirect you back to this application.")
    else:
        if check_token():
            st.success("Connected to DocuSign")
            
            # Display token information
            token_data = st.session_state.token_data
            with st.expander("View Token Information"):
                st.json({
                    "access_token": token_data['access_token'][:20] + "...",
                    "expires_in": token_data['expires_in'],
                    "token_type": token_data['token_type']
                })

            # Account ID input
            account_id = st.text_input("Enter your DocuSign Account ID")
            
            if account_id:
                # Get configurations if not already loaded
                if not st.session_state.configs:
                    with st.spinner("Loading DocGen configurations..."):
                        configs = get_docgen_configurations(account_id)
                        if configs:
                            st.session_state.configs = configs
                
                # Display configuration selection
                if st.session_state.configs:
                    # Create initial list of configuration names and their hrefs
                    config_options = {}
                    for config in st.session_state.configs.get('Items', []):
                        name = config.get('Name', '')
                        config_id = config.get('Id', '')
                        href = config.get('Href')
                        display_name = f"{name} ({config_id})" if name and config_id else name or 'Unnamed'
                        config_options[display_name] = href
                    
                    # Configuration selection
                    selected_config_name = st.selectbox(
                        "Select DocGen Configuration",
                        options=list(config_options.keys()),
                        key="config_selector"
                    )

                    # Search functionality (optional)
                    show_search = st.checkbox("Enable Search")
                    if show_search:
                        search_term = st.text_input("Search Configurations", "").lower()
                        # Filter options based on search
                        if search_term:
                            filtered_options = {k: v for k, v in config_options.items() if search_term in k.lower()}
                            st.write(f"Found {len(filtered_options)} configurations matching search")
                            selected_config_name = st.selectbox(
                                "Filtered Configurations",
                                options=list(filtered_options.keys()),
                                key="filtered_selector"
                            )
                    
                    if selected_config_name:
                        st.session_state.selected_config = config_options[selected_config_name]
                        
                        # XML Payload input
                        xml_payload = st.text_area(
                            "Enter XML Payload",
                            value='<Params><Source>CLM API Example</Source></Params>',
                            height=150
                        )
                        
                        # Create task button
                        if st.button("Create DocLauncher Task"):
                            if not xml_payload:
                                st.error("Please enter an XML payload")
                            else:
                                create_doc_launcher_task(
                                    account_id,
                                    st.session_state.selected_config,
                                    xml_payload
                                )

            if st.button("Disconnect"):
                # Delete the token file
                auth_handler.delete_token()
                # Clear session state
                st.session_state.authenticated = False
                st.session_state.token_data = None
                st.session_state.configs = None
                st.session_state.selected_config = None
                logger.info("User disconnected from DocuSign")
                st.rerun()

if __name__ == "__main__":
    main()
