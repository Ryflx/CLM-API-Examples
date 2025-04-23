# DocuSign CLM API Examples - File Index

This document provides a comprehensive index of all files in the DocuSign CLM API Examples project, their purposes, and their relationships.

## Project Structure

```
CLM-API-Examples/
├── .git/                    # Git repository data
├── .gitignore               # Git ignore configuration
├── .streamlit/              # Streamlit configuration
├── .tokens/                 # Directory for storing authentication tokens
├── docs/                    # Documentation
│   ├── blueprint.md         # Project blueprint and roadmap
│   └── sourcing.xml         # Example XML for sourcing use case
├── logs/                    # Application logs
├── src/                     # Source code
│   ├── app.py               # Main Streamlit application
│   ├── docusign_auth.py     # DocuSign authentication module
│   └── image/               # UI images
├── ssl/                     # SSL certificates for HTTPS
├── .env                     # Environment variables
├── README.md                # Project documentation
└── requirements.txt         # Python dependencies
```

## Key Files

### Configuration Files

- **`.env`**: Contains environment variables for DocuSign integration:
  - DOCUSIGN_CLIENT_ID
  - DOCUSIGN_CLIENT_SECRET
  - DOCUSIGN_ACCOUNT_ID
  - DOCUSIGN_AUTH_SERVER
  - DOCUSIGN_OAUTH_BASE_URL
  - DOCUSIGN_REDIRECT_URI

- **`requirements.txt`**: Lists Python dependencies:
  - streamlit>=1.29.0
  - python-dotenv>=1.0.0
  - requests>=2.31.0
  - docusign-esign>=3.25.0

### Source Code

- **`src/app.py`**: Main Streamlit application (1112 lines)
  - Handles UI rendering and user interactions
  - Implements DocuSign CLM API integration
  - Manages authentication flow
  - Implements DocLauncher task creation
  - Provides document attribute retrieval
  - Includes sourcing use case implementation

- **`src/docusign_auth.py`**: DocuSign authentication module (122 lines)
  - Manages OAuth 2.0 authentication flow
  - Handles token acquisition and refresh
  - Provides token validation and storage
  - Manages credential retrieval from various sources

### Documentation

- **`README.md`**: Main project documentation (351 lines)
  - Installation instructions
  - Docker setup
  - Security and HTTPS configuration
  - Usage instructions
  - Troubleshooting

- **`docs/blueprint.md`**: Project blueprint and roadmap (229 lines)
  - Project overview
  - Current status
  - Technology stack
  - Feature list (current and planned)
  - Implementation details
  - API integration points

- **`docs/sourcing.xml`**: Example XML for sourcing use case (11 lines)
  - Template for XML payload in sourcing use case

## Functionality Overview

### Authentication Flow
1. User initiates authentication via UI
2. Application redirects to DocuSign OAuth consent screen
3. User authorizes the application
4. DocuSign redirects back with authorization code
5. Application exchanges code for access token
6. Token is stored for future API calls
7. Token refresh is handled automatically

### DocLauncher Task Creation
1. User selects DocLauncher configuration
2. User provides XML payload
3. Application creates DocLauncher task via CLM API
4. Result URL is displayed to user

### Document Attribute Retrieval
1. User provides document ID
2. Application retrieves document attributes via CLM API
3. Attributes are displayed with search/filter capability

### Sourcing Use Case
1. User selects customer and enters form data
2. Application generates XML payload
3. XML is used to create DocLauncher task
4. Result is displayed to user

## Dependencies and Relationships

- `app.py` imports `docusign_auth.py` for authentication handling
- Both modules rely on environment variables from `.env`
- Authentication tokens are stored in `.tokens/` directory
- Application logs are written to `logs/` directory
- SSL certificates in `ssl/` enable HTTPS for secure OAuth flow

## Development and Deployment

The application is designed to be run in a Docker container with:
- Self-signed SSL certificates for HTTPS
- Volume mounts for persistent storage of tokens and logs
- Environment variables for configuration

## Security Considerations

- OAuth 2.0 for secure authentication
- HTTPS with SSL certificates
- Token refresh mechanism
- Secure storage of credentials
- No hardcoded secrets 