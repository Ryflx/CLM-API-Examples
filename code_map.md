# DocuSign CLM API Examples - Code Map

This document provides a detailed map of the code structure, showing the relationships between different components and the flow of execution.

## Application Architecture

```
┌─────────────────────────────────┐
│           Streamlit UI          │
│        (src/app.py - main)      │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│      Authentication Flow         │
│   (src/docusign_auth.py)        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│        DocuSign CLM API         │
│     (External Integration)      │
└─────────────────────────────────┘
```

## Component Breakdown

### 1. Main Application (src/app.py)

The main application is structured into several logical components:

```
┌─────────────────────────────────────────────────────┐
│                   src/app.py                        │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────────────┐   │
│ │  Configuration  │  │  Authentication Logic   │   │
│ │  & Setup        │  │  (handle_callback,      │   │
│ │  (get_config,   │  │   check_token)          │   │
│ │   logging)      │  │                         │   │
│ └─────────────────┘  └─────────────────────────┘   │
│                                                     │
│ ┌─────────────────┐  ┌─────────────────────────┐   │
│ │  API Functions  │  │  UI Components          │   │
│ │  (get_docgen,   │  │  (show_docgen_interface,│   │
│ │   create_task,  │  │   show_catalog,         │   │
│ │   get_attributes)│  │   show_sourcing)       │   │
│ └─────────────────┘  └─────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐    │
│ │              Main Function                  │    │
│ │  (Routing logic and application flow)       │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 2. Authentication Module (src/docusign_auth.py)

```
┌─────────────────────────────────────────────────────┐
│               src/docusign_auth.py                  │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────────────┐   │
│ │  Initialization │  │  Credential Management  │   │
│ │  (__init__)     │  │  (_get_credentials)     │   │
│ └─────────────────┘  └─────────────────────────┘   │
│                                                     │
│ ┌─────────────────┐  ┌─────────────────────────┐   │
│ │  OAuth Flow     │  │  Token Management       │   │
│ │  (get_consent,  │  │  (_save_token,          │   │
│ │   get_token)    │  │   load_token,           │   │
│ └─────────────────┘  │   is_token_valid)       │   │
│                      └─────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Execution Flow

### 1. Application Startup

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Load .env   │────▶│ Initialize  │────▶│ Setup       │
│ variables   │     │ logging     │     │ Streamlit   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Initialize  │◀────│ Check for   │◀────│ Run main()  │
│ DocuSignAuth│     │ auth state  │     │ function    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 2. Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ User clicks │────▶│ Generate    │────▶│ Redirect to │
│ "Connect"   │     │ consent URL │     │ DocuSign    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Store token │◀────│ Exchange    │◀────│ Callback    │
│ data        │     │ code for    │     │ with code   │
└─────────────┘     │ token       │     └─────────────┘
```

### 3. DocLauncher Task Creation

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ User selects│────▶│ User enters │────▶│ Create      │
│ DocGen      │     │ XML payload │     │ DocLauncher │
│ config      │     │             │     │ task        │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Display     │
                                        │ result URL  │
                                        └─────────────┘
```

### 4. Document Attributes Retrieval

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ User enters │────▶│ Fetch       │────▶│ Filter and  │
│ document ID │     │ attributes  │     │ display     │
└─────────────┘     └─────────────┘     │ attributes  │
                                        └─────────────┘
```

### 5. Sourcing Use Case

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ User selects│────▶│ User fills  │────▶│ Generate    │
│ customer    │     │ form data   │     │ XML payload │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Display     │◀────│ Create      │◀────│ Select      │
│ result      │     │ DocLauncher │     │ DocGen      │
│             │     │ task        │     │ config      │
└─────────────┘     └─────────────┘     └─────────────┘
```

## API Integration Points

### DocuSign CLM API Endpoints Used

1. **OAuth Endpoints**
   - `https://{auth_server}/oauth/auth` - Authorization request
   - `https://{auth_server}/oauth/token` - Token exchange and refresh

2. **CLM API Endpoints**
   - `/spring-api/v1/accounts/{accountId}/docgen/configurations` - Get DocGen configurations
   - `/spring-api/v1/accounts/{accountId}/doclauncher/tasks` - Create DocLauncher task
   - `/spring-api/v1/accounts/{accountId}/documents/{documentId}/attributes` - Get document attributes

## Error Handling

The application implements comprehensive error handling:

1. **Authentication Errors**
   - Token refresh failures
   - Invalid credentials
   - Authorization failures

2. **API Errors**
   - Network errors with retry mechanism
   - Rate limiting handling
   - Invalid request handling

3. **UI Error Feedback**
   - User-friendly error messages
   - Detailed logging for debugging

## Logging System

```
┌─────────────────────────────────────────────────────┐
│                  Logging System                     │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────────────┐   │
│ │  File Logging   │  │  Console Logging        │   │
│ │  (Daily logs)   │  │  (Development)          │   │
│ └─────────────────┘  └─────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐    │
│ │              API Call Logging               │    │
│ │  (Request/Response details, errors)         │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

The logging system captures:
- API requests and responses
- Authentication events
- Error conditions
- User actions 