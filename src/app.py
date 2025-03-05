import streamlit as st
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from docusign_auth import DocuSignAuth
import webbrowser
import json
import requests

# GitHub raw content URLs
REPO_URL = "https://raw.githubusercontent.com/Ryflx/CLM-API-Examples/main"
FEATURE_IMAGES = {
    "form": f"{REPO_URL}/src/image/form.png",
    "metadata": f"{REPO_URL}/src/image/metadata.png",
    "add-document": f"{REPO_URL}/src/image/add-document.png",
    "work-in-progress": f"{REPO_URL}/src/image/work-in-progress.png"
}

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

def get_docgen_configurations(account_id, max_retries=3):
    """Get list of docgen configurations with pagination support"""
    try:
        headers = {
            'Authorization': f"Bearer {st.session_state.token_data['access_token']}",
            'Content-Type': 'application/json'
        }

        all_items = []
        next_url = f"https://apiuatna11.springcm.com/v2/{account_id}/doclauncherconfigurations?limit=100"

        while next_url:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    log_api_call("GET", next_url)
                    response = requests.get(next_url, headers=headers)
                    
                    # Check if we got a 500 error
                    if response.status_code == 500:
                        retry_count += 1
                        if retry_count < max_retries:
                            st.warning(f"Server error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                            continue
                        else:
                            st.error("Maximum retries reached. Please try again later.")
                            return None
                    
                    # For other errors, try to get more details
                    if response.status_code != 200:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('Message', response.text)
                        except:
                            error_msg = response.text
                        st.error(f"API Error ({response.status_code}): {error_msg}")
                        return None
                    
                    response_data = response.json()
                    log_api_call("GET", next_url, response_data=response_data)
                    
                    if 'Items' in response_data:
                        all_items.extend(response_data['Items'])
                    
                    # Check if there are more pages
                    next_url = response_data.get('Next')
                    if next_url:
                        st.write(f"Fetching more configurations... ({len(all_items)} so far)")
                    
                    break  # Success, exit retry loop
                    
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        st.warning(f"Connection error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                        continue
                    else:
                        st.error(f"Failed to connect after {max_retries} attempts: {str(e)}")
                        return None

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

def create_doc_launcher_task(account_id, config_href, xml_payload, max_retries=3):
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
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                log_api_call("POST", endpoint, request_data=data)
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=data
                )
                
                # Check if we got a 500 error
                if response.status_code == 500:
                    retry_count += 1
                    if retry_count < max_retries:
                        st.warning(f"Server error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                        continue
                    else:
                        st.error("Maximum retries reached. Please try again later.")
                        return None
                
                try:
                    response_data = response.json()
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
                
                break  # Success, exit retry loop
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    st.warning(f"Connection error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                    continue
                else:
                    st.error(f"Failed to connect after {max_retries} attempts: {str(e)}")
                    return None
            
        response.raise_for_status()
        log_api_call("POST", endpoint, response_data=response_data)
        st.success("DocLauncher task created successfully!")
        logger.info(f"DocLauncher task created successfully: {response_data}")
        
        # Display Status first
        if "Status" in response_data:
            status = response_data['Status']
            if status == "Success":
                st.success(f"Status: {status}")
            else:
                st.warning(f"Status: {status}")

        # Display the DocLauncher Result URL
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
                    st.info("Opening DocLauncher in a new tab...")
                    webbrowser.open_new_tab(response.url)
                    st.info("If the tab doesn't open automatically, click the link below:")
                    st.markdown(f"[Open DocLauncher]({response.url})")
                else:
                    st.error(f"Failed to get DocLauncher URL: {response.status_code}")
            except Exception as e:
                st.error(f"Error accessing DocLauncher: {str(e)}")

        # Display the full response in expander
        with st.expander("View Full Response"):
            st.json(response_data)

        return response_data

    except Exception as e:
        error_msg = f"Failed to create DocLauncher task: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

def get_document_attributes(account_id, doc_id, max_retries=3):
    """Get document attributes using CLM API"""
    try:
        headers = {
            'Authorization': f"Bearer {st.session_state.token_data['access_token']}",
            'Content-Type': 'application/json'
        }
        
        endpoint = f"https://apiuatna11.springcm.com/v2/{account_id}/documents/{doc_id}?expand=AttributeGroups"
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                log_api_call("GET", endpoint)
                response = requests.get(endpoint, headers=headers)
                
                # Check if we got a 500 error
                if response.status_code == 500:
                    retry_count += 1
                    if retry_count < max_retries:
                        st.warning(f"Server error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                        continue
                    else:
                        st.error("Maximum retries reached. Please try again later.")
                        return None
                
                # For other errors, try to get more details
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('Message', response.text)
                    except:
                        error_msg = response.text
                    st.error(f"API Error ({response.status_code}): {error_msg}")
                    return None
                
                response_data = response.json()
                log_api_call("GET", endpoint, response_data=response_data)
                return response_data
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    st.warning(f"Connection error, retrying... (Attempt {retry_count + 1}/{max_retries})")
                    continue
                else:
                    st.error(f"Failed to connect after {max_retries} attempts: {str(e)}")
                    return None

    except Exception as e:
        error_msg = f"Failed to get document attributes: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

def filter_attributes(data, search_term):
    """Recursively search through nested JSON for matching attributes"""
    results = []
    search_term = search_term.lower()
    
    def search_recursive(obj, path=None):
        if path is None:
            path = []
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = path + [key]
                
                # Check if this key-value pair matches
                if isinstance(value, str) and search_term in value.lower():
                    results.append({
                        'path': current_path,
                        'key': key,
                        'value': value,
                        'full_path': ' > '.join(current_path)
                    })
                elif isinstance(key, str) and search_term in key.lower():
                    results.append({
                        'path': current_path,
                        'key': key,
                        'value': value,
                        'full_path': ' > '.join(current_path)
                    })
                
                # Continue searching deeper
                search_recursive(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = path + [f"[{i}]"]
                search_recursive(item, current_path)
    
    search_recursive(data)
    return results

def display_filtered_results(filtered_results, search_term):
    """Display filtered attribute results with highlighting in a simplified format"""
    if not filtered_results:
        st.info(f"No matches found for '{search_term}'")
        return
    
    st.success(f"Found {len(filtered_results)} matches for '{search_term}'")
    
    # Display results in a simple list format
    for item in filtered_results:
        # Display the key-value pair with highlighting
        key = item['key']
        value = item['value']
        
        if isinstance(value, str):
            # Highlight the matching text in the value
            highlighted_value = value.replace(
                search_term, 
                f"<span style='background-color: yellow; color: black;'>{search_term}</span>"
            )
            st.markdown(f"**{key}:** {highlighted_value}", unsafe_allow_html=True)
        else:
            # For non-string values, just display as is
            st.markdown(f"**{key}:** {value}")

def show_document_attributes_interface():
    """Show the document attributes interface"""
    # Add back button
    if st.button("← Back to Catalog"):
        st.session_state.current_view = 'catalog'
        st.rerun()
        
    st.title("Get Document Attributes")
    st.write("Enter a Document ID to retrieve its attributes")
    
    # Document ID input
    doc_id = st.text_input("Enter Document ID")
    
    # Get attributes button
    if st.button("Get Attributes"):
        if not doc_id:
            st.error("Please enter a Document ID")
        else:
            with st.spinner("Retrieving document attributes..."):
                result = get_document_attributes(
                    st.session_state.account_id,
                    doc_id
                )
                if result:
                    st.success("Document attributes retrieved successfully!")
                    # Store the result in session state for searching
                    st.session_state.document_attributes = result
    
    # Search functionality (only show if we have document attributes)
    if 'document_attributes' in st.session_state:
        st.subheader("Search Document Attributes")
        st.write("Enter a search term to filter attributes (e.g., 'Status: Contract Review')")
        
        # Search input and options
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("Search Term", key="attribute_search")
        with col2:
            show_full_json = st.checkbox("Show Full JSON", value=False)
        
        # Perform search if we have a search term
        if search_term:
            filtered_results = filter_attributes(st.session_state.document_attributes, search_term)
            display_filtered_results(filtered_results, search_term)
        
        # Option to show full JSON
        if show_full_json or not search_term:
            with st.expander("Full JSON Response", expanded=not search_term):
                st.json(st.session_state.document_attributes)

def get_actual_redirect_uri():
    """Get the actual redirect URI based on how the app is being accessed"""
    # Get the URL where the app is being accessed
    base_url = st.query_params.get('base_url', None)
    if not base_url:
        # Default to secrets/environment variable if no base_url provided
        return get_config('DOCUSIGN_REDIRECT_URI')
    return base_url

def show_feature_card(title, description, is_active=False, image_name=None):
    """Helper function to create a consistent feature card"""
    # Card and button styling
    st.markdown("""
        <style>
            .feature-card {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                background-color: white;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            .feature-title {
                margin: 15px 0;
                font-size: 1.2em;
                font-weight: bold;
            }
            .feature-description {
                margin: 10px 0;
                min-height: 60px;
                color: #666;
            }
            /* Custom button styling */
            .stButton > button {
                width: 100%;
                height: 3rem;
                line-height: 1;
                padding: 0 1.5rem;
                font-size: 1rem;
                font-weight: 500;
                border-radius: 8px;
                transition: all 0.3s ease;
                margin-top: 1rem;
                display: flex !important;
                align-items: center;
                justify-content: center;
                white-space: nowrap;
            }
            /* Active button */
            .stButton > button:not([disabled]) {
                background-color: #00b4e6;
                color: white;
                border: none;
                box-shadow: 0 2px 4px rgba(0, 180, 230, 0.2);
            }
            .stButton > button:not([disabled]):hover {
                background-color: #0099cc;
                box-shadow: 0 4px 8px rgba(0, 180, 230, 0.3);
                transform: translateY(-1px);
            }
            /* Disabled button */
            .stButton > button[disabled] {
                background-color: #f5f5f5;
                color: #999;
                border: 1px solid #ddd;
                cursor: not-allowed;
                opacity: 0.8;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Create card container
    with st.container():
        # Use GitHub raw URL if image name provided, otherwise use placeholder
        image_url = FEATURE_IMAGES.get(image_name.split('.')[0]) if image_name else "https://via.placeholder.com/150"
        st.markdown(f"""
            <div class="feature-card">
                <img src="{image_url}" style="max-width:150px; height:150px; object-fit:contain; margin:auto;">
                <div class="feature-title">{title}</div>
                <div class="feature-description">{description}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Center the button using columns
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if is_active:
                if st.button("Get Started", key=f"btn_{title.lower().replace(' ', '_')}_active", use_container_width=True):
                    if title == "Launch DocGen Form":
                        st.session_state.current_view = 'docgen'
                    elif title == "Get Document Attributes":
                        st.session_state.current_view = 'document_attributes'
                    elif title == "Sourcing Login":
                        st.session_state.current_view = 'sourcing_login'
                    st.rerun()
            else:
                st.button("Coming Soon", key=f"btn_{title.lower().replace(' ', '_')}_disabled", disabled=True, use_container_width=True)

def show_catalog():
    """Display the catalog of available features"""
    st.title("Available Features")
    
    # Add spacing between title and cards
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Style for columns
    st.markdown("""
        <style>
            .stColumns {
                gap: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # First row of three features
    cols = st.columns(3, gap="large")
    with cols[0]:
        show_feature_card(
            "Launch DocGen Form",
            "Create documents using DocGen configurations",
            is_active=True,
            image_name="form.png"
        )
    with cols[1]:
        show_feature_card(
            "Get Document Attributes",
            "Retrieve and view document attributes and metadata",
            is_active=True,
            image_name="metadata.png"
        )
    with cols[2]:
        show_feature_card(
            "Update a Document",
            "Update document properties and metadata",
            image_name="add-document.png"
        )
    
    # Add spacing between rows
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Second row of three features (new)
    cols2 = st.columns(3, gap="large")
    with cols2[0]:
        show_feature_card(
            "Kick off workflow",
            "Start a workflow in DocuSign CLM",
            is_active=False,
            image_name="work-in-progress.png"
        )
    with cols2[1]:
        show_feature_card(
            "XML Merge",
            "Merge XML data with document templates",
            is_active=False,
            image_name="work-in-progress.png"
        )
    with cols2[2]:
        show_feature_card(
            "Sourcing Login",
            "Onboard a new Supplier",
            is_active=True,
            image_name="work-in-progress.png"
        )

def show_docgen_interface():
    """Show the DocGen form interface"""
    # Add back button
    if st.button("← Back to Catalog"):
        st.session_state.current_view = 'catalog'
        st.rerun()
        
    st.title("Launch DocGen Form")
    st.write("Enter details below to pull and kick off a Doc Gen Form")
    
    # Get configurations if not already loaded
    if not st.session_state.configs:
        with st.spinner("Loading DocGen configurations..."):
            configs = get_docgen_configurations(st.session_state.account_id)
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
                        st.session_state.account_id,
                        st.session_state.selected_config,
                        xml_payload
                    )

def show_sourcing_login_interface():
    """Show the sourcing login interface"""
    # Add back button
    if st.button("← Back to Catalog"):
        st.session_state.current_view = 'catalog'
        st.rerun()
        
    st.title("Sourcing System Login")
    st.write("Enter your credentials to access the sourcing system")
    
    # Login form
    with st.form("sourcing_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
    
    if login_button:
        # Any credentials are accepted
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            st.success(f"Welcome, {username}!")
            # Move to the use case selection page
            st.session_state.sourcing_username = username
            st.session_state.current_view = 'sourcing_use_case'
            st.rerun()

import xml.etree.ElementTree as ET
from io import StringIO

# Define agreement types
AGREEMENT_TYPES = [
    "Purchasing Agreement",
    "Master Services Agreement",
    "Statement of Work"
]

# Store dummy customer data
DUMMY_CUSTOMERS = [
    {
        "name": "ABC Company",
        "billing": {
            "address": "45 North Avenue",
            "city": "London",
            "state": "Greater London",
            "postal_code": "E1 2YC",
            "country": "United Kingdom"
        }
    },
    {
        "name": "XYZ Corporation",
        "billing": {
            "address": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "United States"
        }
    },
    {
        "name": "Acme Industries",
        "billing": {
            "address": "789 Industrial Blvd",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60601",
            "country": "United States"
        }
    },
    {
        "name": "Global Enterprises",
        "billing": {
            "address": "1 Business Park",
            "city": "Singapore",
            "state": "Central Region",
            "postal_code": "018956",
            "country": "Singapore"
        }
    },
    {
        "name": "Tech Innovations Ltd",
        "billing": {
            "address": "42 Innovation Way",
            "city": "Berlin",
            "state": "Berlin",
            "postal_code": "10115",
            "country": "Germany"
        }
    }
]

# Initialize sourcing data in session state if not already present
def init_sourcing_data():
    if 'sourcing_data' not in st.session_state:
        st.session_state.sourcing_data = {
            "agreement_type": "",
            "customer": None
        }

# Function to convert the session state data to XML format for API submission
def dict_to_sourcing_xml():
    """Convert the sourcing data from session state to XML format for API submission"""
    init_sourcing_data()
    
    if not st.session_state.sourcing_data["customer"]:
        return ""
    
    customer = st.session_state.sourcing_data["customer"]
    agreement_type = st.session_state.sourcing_data["agreement_type"]
    
    xml_template = """<?xml version="1.0" encoding="utf-16" standalone="yes"?>
<TemplateFieldData displayName="" displayValue="">
  <Agreement_Type>{agreement_type}</Agreement_Type>
  <Account_Name>{customer[name]}</Account_Name>
  <Billing_Address>{customer[billing][address]}</Billing_Address>
  <Billing_City>{customer[billing][city]}</Billing_City>
  <Billing_State>{customer[billing][state]}</Billing_State>
  <Billing_Postal_Code>{customer[billing][postal_code]}</Billing_Postal_Code>
  <Billing_Country>{customer[billing][country]}</Billing_Country>
</TemplateFieldData>"""
    
    return xml_template.format(
        agreement_type=agreement_type,
        customer=customer
    )

def show_sourcing_use_case_interface():
    """Show the agreement type selection interface"""
    # Initialize sourcing data
    init_sourcing_data()
    
    # Add back button
    if st.button("← Back to Login"):
        st.session_state.current_view = 'sourcing_login'
        st.rerun()
        
    st.title("Select Agreement Type")
    st.write(f"Welcome, {st.session_state.sourcing_username}. Please select an agreement type to proceed.")
    
    # Agreement type selection
    agreement_type = st.selectbox(
        "Select Agreement Type",
        AGREEMENT_TYPES,
        index=0
    )
    
    if st.button("Continue"):
        # Store the selected agreement type in session state
        st.session_state.sourcing_data["agreement_type"] = agreement_type
        st.session_state.current_view = 'customer_selection'
        st.rerun()

def show_customer_selection_interface():
    """Show the customer selection interface"""
    # Initialize sourcing data
    init_sourcing_data()
    
    # Add back button
    if st.button("← Back to Agreement Type"):
        st.session_state.current_view = 'sourcing_use_case'
        st.rerun()
        
    st.title("Select Customer")
    st.write("Please select a customer to proceed.")
    
    # Create a list of customer names for the dropdown
    customer_names = [customer["name"] for customer in DUMMY_CUSTOMERS]
    
    # Customer selection
    selected_customer = st.selectbox(
        "Select Customer",
        customer_names,
        index=0
    )
    
    if st.button("Continue"):
        # Find the selected customer in the DUMMY_CUSTOMERS list
        for customer in DUMMY_CUSTOMERS:
            if customer["name"] == selected_customer:
                # Store the customer in session state
                st.session_state.sourcing_data["customer"] = customer
                break
        
        # Generate XML from our session state data
        st.session_state.sourcing_xml_data = dict_to_sourcing_xml()
        st.session_state.current_view = 'sourcing_form'
        st.rerun()

def show_sourcing_form_interface():
    """Show the sourcing form interface with pre-filled data"""
    # Initialize sourcing data
    init_sourcing_data()
    
    # Add back button
    if st.button("← Back to Customer Selection"):
        st.session_state.current_view = 'customer_selection'
        st.rerun()
        
    st.title("Pre-populated Form Data")
    st.write("The following information has been pre-populated from the internal system")
    
    # Check if customer data exists in session state
    if not st.session_state.sourcing_data["customer"]:
        st.error("No customer data found. Please go back and select a customer.")
        return
    
    customer = st.session_state.sourcing_data["customer"]
    
    # Display only the required pre-filled fields
    st.subheader("Agreement Information")
    st.write(f"**Agreement Type:** {st.session_state.sourcing_data['agreement_type']}")
    
    st.subheader("Customer Information")
    st.write(f"**Account Name:** {customer['name']}")
    st.write(f"**Billing Address:** {customer['billing']['address']}")
    st.write(f"**Billing City:** {customer['billing']['city']}")
    st.write(f"**Billing State:** {customer['billing']['state']}")
    st.write(f"**Billing Postal Code:** {customer['billing']['postal_code']}")
    st.write(f"**Billing Country:** {customer['billing']['country']}")
    
    # Display the XML that will be sent
    with st.expander("View XML Payload"):
        st.code(st.session_state.sourcing_xml_data, language="xml")
    
    # Get configurations if not already loaded
    if not st.session_state.configs:
        with st.spinner("Loading DocGen configurations..."):
            configs = get_docgen_configurations(st.session_state.account_id)
            if configs:
                st.session_state.configs = configs
    
    # Configuration selection if configs are loaded
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
            key="sourcing_config_selector"
        )
        
        if selected_config_name:
            st.session_state.selected_config = config_options[selected_config_name]
            
            # Submit button
            if st.button("Submit Agreement"):
                # Use the XML data from the dictionary
                xml_payload = st.session_state.sourcing_xml_data
                
                # Create the DocLauncher task
                result = create_doc_launcher_task(
                    st.session_state.account_id,
                    st.session_state.selected_config,
                    xml_payload
                )
                
                if result:
                    # Add a button to return to catalog
                    if st.button("Return to Catalog"):
                        st.session_state.current_view = 'catalog'
                        st.rerun()

def main():
    # Add JavaScript for auto-hiding messages
    st.markdown("""
        <script>
            function hideMessages() {
                const messages = document.querySelectorAll('.stSuccess, .stInfo');
                messages.forEach(msg => {
                    setTimeout(() => {
                        msg.style.transition = 'opacity 1s';
                        msg.style.opacity = '0';
                        setTimeout(() => msg.style.display = 'none', 1000);
                    }, 5000);
                });
            }
            
            // Run on initial load
            hideMessages();
            
            // Create observer to handle dynamically added messages
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.classList && 
                            (node.classList.contains('stSuccess') || 
                             node.classList.contains('stInfo'))) {
                            setTimeout(() => {
                                node.style.transition = 'opacity 1s';
                                node.style.opacity = '0';
                                setTimeout(() => node.style.display = 'none', 1000);
                            }, 5000);
                        }
                    });
                });
            });
            
            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        </script>
    """, unsafe_allow_html=True)
    
    st.image("https://cf-images.us-east-1.prod.boltdns.net/v1/static/6118377982001/f500d879-d469-4a49-851c-0337de041880/7c4ad13a-f83b-4e57-8cbc-7997519f8c96/1280x720/match/image.jpg?v=20250205.7")
    st.title("DocuSign CLM Integration")

    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'configs' not in st.session_state:
        st.session_state.configs = None
    if 'selected_config' not in st.session_state:
        st.session_state.selected_config = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'catalog'

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
        
        # DocuSign Configuration Inputs before authentication
        with st.form("docusign_config"):
            st.subheader("DocuSign Configuration")
            st.info("Please enter your DocuSign credentials to connect")
            client_id = st.text_input("Enter your DocuSign Integration Key (Client ID)", type="password")
            client_secret = st.text_input("Enter your DocuSign Secret Key", type="password")
            
            connect_button = st.form_submit_button("Connect to DocuSign")
            
        if connect_button:
            if not client_id or not client_secret:
                st.error("Please fill in Integration Key and Secret Key")
            else:
                # Store credentials in session state
                st.session_state.client_id = client_id
                st.session_state.client_secret = client_secret
                
                try:
                    redirect_uri = get_actual_redirect_uri()
                    consent_url = auth_handler.get_consent_url(redirect_uri)
                    logger.info(f"Opening DocuSign consent URL: {consent_url}")
                    webbrowser.open_new_tab(consent_url)
                    st.info("Opening DocuSign authentication in a new tab...")
                    st.info("If the tab doesn't open automatically, click the link below:")
                    st.markdown(f"[Open DocuSign Authentication]({consent_url})")
                    st.info("After authentication, you will be redirected back to this application.")
                except Exception as e:
                    st.error(f"Failed to connect: {str(e)}")
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

            # Check for account ID
            if not hasattr(st.session_state, 'account_id'):
                with st.form("account_id_form"):
                    st.info("Please enter your DocuSign Account ID to continue")
                    new_account_id = st.text_input("Enter your DocuSign Account ID")
                    submit_account = st.form_submit_button("Save Account ID")
                
                if submit_account:
                    if not new_account_id:
                        st.error("Please enter your Account ID")
                    else:
                        st.session_state.account_id = new_account_id
                        st.rerun()
            else:
                # Show either catalog or specific interface
                if st.session_state.current_view == 'catalog':
                    show_catalog()
                elif st.session_state.current_view == 'docgen':
                    show_docgen_interface()
                elif st.session_state.current_view == 'document_attributes':
                    show_document_attributes_interface()
                elif st.session_state.current_view == 'sourcing_login':
                    show_sourcing_login_interface()
                elif st.session_state.current_view == 'sourcing_use_case':
                    show_sourcing_use_case_interface()
                elif st.session_state.current_view == 'customer_selection':
                    show_customer_selection_interface()
                elif st.session_state.current_view == 'sourcing_form':
                    show_sourcing_form_interface()

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
