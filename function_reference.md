# DocuSign CLM API Examples - Function Reference

This document provides a detailed reference of the key functions in the codebase, their parameters, return values, and usage examples.

## Authentication Module (src/docusign_auth.py)

### DocuSignAuth Class

#### `__init__()`

Initializes the DocuSign authentication handler.

**Parameters:** None

**Usage:**
```python
auth_handler = DocuSignAuth()
```

#### `_get_credentials()`

Gets credentials from session state or fallback to secrets/env.

**Returns:**
- `client_id` (str): DocuSign Integration Key
- `client_secret` (str): DocuSign Secret Key
- `account_id` (str): DocuSign Account ID

**Usage:**
```python
client_id, client_secret, account_id = auth_handler._get_credentials()
```

#### `get_consent_url(redirect_uri=None)`

Generates the consent URL for DocuSign OAuth.

**Parameters:**
- `redirect_uri` (str, optional): The redirect URI for OAuth callback

**Returns:**
- `url` (str): The consent URL for DocuSign OAuth

**Usage:**
```python
consent_url = auth_handler.get_consent_url("https://localhost:8501")
```

#### `get_token_from_code(code, redirect_uri=None)`

Exchanges authorization code for access token.

**Parameters:**
- `code` (str): The authorization code from DocuSign
- `redirect_uri` (str, optional): The redirect URI for OAuth callback

**Returns:**
- `token_data` (dict): The token data including access_token, refresh_token, etc.

**Usage:**
```python
token_data = auth_handler.get_token_from_code(code, "https://localhost:8501")
```

#### `refresh_token(refresh_token)`

Refreshes the access token using refresh token.

**Parameters:**
- `refresh_token` (str): The refresh token

**Returns:**
- `token_data` (dict): The new token data

**Usage:**
```python
new_token_data = auth_handler.refresh_token(token_data['refresh_token'])
```

#### `is_token_valid(token_data)`

Checks if the current token is valid.

**Parameters:**
- `token_data` (dict): The token data to check

**Returns:**
- `valid` (bool): True if token is valid, False otherwise

**Usage:**
```python
if auth_handler.is_token_valid(token_data):
    # Use token
else:
    # Refresh token
```

## Main Application (src/app.py)

### Configuration and Setup

#### `get_config(key)`

Gets configuration from Streamlit secrets or environment variables.

**Parameters:**
- `key` (str): The configuration key to get

**Returns:**
- `value` (str): The configuration value

**Usage:**
```python
client_id = get_config("DOCUSIGN_CLIENT_ID")
```

#### `serialize_for_logging(obj)`

Converts objects to JSON-serializable format.

**Parameters:**
- `obj` (any): The object to serialize

**Returns:**
- `serialized` (any): The serialized object

**Usage:**
```python
serialized_data = serialize_for_logging(response_data)
```

#### `log_api_call(method, endpoint, request_data=None, response_data=None, error=None)`

Logs API call details.

**Parameters:**
- `method` (str): The HTTP method (GET, POST, etc.)
- `endpoint` (str): The API endpoint
- `request_data` (any, optional): The request data
- `response_data` (any, optional): The response data
- `error` (Exception, optional): Any error that occurred

**Usage:**
```python
log_api_call("POST", "/spring-api/v1/accounts/{accountId}/doclauncher/tasks", 
             request_data=payload, response_data=response)
```

### Authentication Logic

#### `handle_callback()`

Handles the OAuth callback.

**Usage:**
```python
handle_callback()  # Called when OAuth redirect occurs
```

#### `check_token()`

Checks and refreshes token if necessary.

**Usage:**
```python
check_token()  # Called before making API calls
```

### API Functions

#### `get_docgen_configurations(account_id, max_retries=3)`

Fetches DocGen configurations from CLM API.

**Parameters:**
- `account_id` (str): The DocuSign account ID
- `max_retries` (int, optional): Maximum number of retries for API call

**Returns:**
- `configurations` (list): List of DocGen configurations

**Usage:**
```python
configs = get_docgen_configurations(account_id)
```

#### `create_doc_launcher_task(account_id, config_href, xml_payload, max_retries=3)`

Creates a DocLauncher task.

**Parameters:**
- `account_id` (str): The DocuSign account ID
- `config_href` (str): The DocGen configuration HREF
- `xml_payload` (str): The XML payload for the task
- `max_retries` (int, optional): Maximum number of retries for API call

**Returns:**
- `result` (dict): The task creation result including result URL

**Usage:**
```python
result = create_doc_launcher_task(account_id, config_href, xml_payload)
```

#### `get_document_attributes(account_id, doc_id, max_retries=3)`

Retrieves document attributes.

**Parameters:**
- `account_id` (str): The DocuSign account ID
- `doc_id` (str): The document ID
- `max_retries` (int, optional): Maximum number of retries for API call

**Returns:**
- `attributes` (dict): The document attributes

**Usage:**
```python
attributes = get_document_attributes(account_id, doc_id)
```

### UI Components

#### `show_docgen_interface()`

Displays the DocGen interface for creating DocLauncher tasks.

**Usage:**
```python
show_docgen_interface()  # Called from main()
```

#### `show_document_attributes_interface()`

Displays the interface for retrieving document attributes.

**Usage:**
```python
show_document_attributes_interface()  # Called from main()
```

#### `show_sourcing_use_case_interface()`

Displays the interface for the sourcing use case.

**Usage:**
```python
show_sourcing_use_case_interface()  # Called from main()
```

#### `show_catalog()`

Displays the feature catalog.

**Usage:**
```python
show_catalog()  # Called from main()
```

### Helper Functions

#### `filter_attributes(data, search_term)`

Filters document attributes based on search term.

**Parameters:**
- `data` (dict): The document attributes
- `search_term` (str): The search term

**Returns:**
- `filtered_results` (list): Filtered attribute paths and values

**Usage:**
```python
filtered = filter_attributes(attributes, "contract")
```

#### `dict_to_sourcing_xml()`

Converts form data to sourcing XML.

**Returns:**
- `xml` (str): The generated XML

**Usage:**
```python
xml = dict_to_sourcing_xml()
```

#### `get_actual_redirect_uri()`

Gets the actual redirect URI based on the current environment.

**Returns:**
- `uri` (str): The redirect URI

**Usage:**
```python
redirect_uri = get_actual_redirect_uri()
```

## Usage Examples

### Complete Authentication Flow

```python
# Initialize authentication handler
auth_handler = DocuSignAuth()

# Generate consent URL
redirect_uri = get_actual_redirect_uri()
consent_url = auth_handler.get_consent_url(redirect_uri)

# Redirect user to consent URL
# ... (user authorizes app) ...

# Handle callback with authorization code
code = st.query_params['code']
token_data = auth_handler.get_token_from_code(code, redirect_uri)
st.session_state.token_data = token_data
st.session_state.authenticated = True

# Check token before API calls
check_token()
```

### Creating a DocLauncher Task

```python
# Get DocGen configurations
account_id = st.session_state.account_id
configurations = get_docgen_configurations(account_id)

# Select configuration
selected_config = st.selectbox("Select DocGen Configuration", 
                              [(c['name'], c['href']) for c in configurations])
config_name, config_href = selected_config

# Get XML payload
xml_payload = st.text_area("XML Payload", height=200)

# Create DocLauncher task
result = create_doc_launcher_task(account_id, config_href, xml_payload)

# Display result
st.success(f"DocLauncher task created successfully!")
st.markdown(f"**Result URL:** [{result['resultUrl']}]({result['resultUrl']})")
```

### Retrieving Document Attributes

```python
# Get document ID
account_id = st.session_state.account_id
doc_id = st.text_input("Document ID")

# Get attributes
attributes = get_document_attributes(account_id, doc_id)

# Filter attributes
search_term = st.text_input("Search Attributes")
filtered_results = filter_attributes(attributes, search_term)

# Display results
display_filtered_results(filtered_results, search_term)
``` 