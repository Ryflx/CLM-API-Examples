# DocuSign CLM API Reference

This document provides a detailed reference of the DocuSign CLM API endpoints used in the application.

## Authentication Endpoints

### OAuth Authorization

**Endpoint:** `https://{auth_server}/oauth/auth`

**Method:** GET

**Description:** Initiates the OAuth 2.0 authorization flow.

**Query Parameters:**
- `response_type` (required): Must be "code"
- `scope` (required): Space-delimited list of requested scopes (e.g., "signature impersonation spring_write spring_read")
- `client_id` (required): Your DocuSign Integration Key
- `redirect_uri` (required): The URI to redirect to after authorization

**Example Request:**
```
GET https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation%20spring_write%20spring_read&client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:8501
```

**Response:**
- Redirects to the DocuSign login page
- After successful authorization, redirects to the specified redirect_uri with an authorization code

### Token Exchange

**Endpoint:** `https://{auth_server}/oauth/token`

**Method:** POST

**Description:** Exchanges an authorization code for an access token.

**Request Body Parameters:**
- `grant_type` (required): Must be "authorization_code"
- `code` (required): The authorization code received from the authorization endpoint
- `client_id` (required): Your DocuSign Integration Key
- `client_secret` (required): Your DocuSign Secret Key
- `redirect_uri` (required): The same redirect URI used in the authorization request

**Example Request:**
```
POST https://account-d.docusign.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=YOUR_AUTH_CODE&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&redirect_uri=https://localhost:8501
```

**Response:**
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "Bearer",
  "refresh_token": "eyJ0eXAi...",
  "expires_in": 28800
}
```

### Token Refresh

**Endpoint:** `https://{auth_server}/oauth/token`

**Method:** POST

**Description:** Refreshes an access token using a refresh token.

**Request Body Parameters:**
- `grant_type` (required): Must be "refresh_token"
- `refresh_token` (required): The refresh token
- `client_id` (required): Your DocuSign Integration Key
- `client_secret` (required): Your DocuSign Secret Key

**Example Request:**
```
POST https://account-d.docusign.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=YOUR_REFRESH_TOKEN&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

**Response:**
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "Bearer",
  "refresh_token": "eyJ0eXAi...",
  "expires_in": 28800
}
```

## CLM API Endpoints

### Get DocGen Configurations

**Endpoint:** `/spring-api/v1/accounts/{accountId}/docgen/configurations`

**Method:** GET

**Description:** Retrieves a list of DocGen configurations.

**Path Parameters:**
- `accountId` (required): The DocuSign account ID

**Headers:**
- `Authorization` (required): Bearer {access_token}

**Example Request:**
```
GET https://clm.docusign.net/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/docgen/configurations
Authorization: Bearer eyJ0eXAi...
```

**Response:**
```json
{
  "configurations": [
    {
      "name": "Configuration 1",
      "href": "/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/docgen/configurations/87654321-4321-4321-4321-210987654321",
      "id": "87654321-4321-4321-4321-210987654321",
      "description": "Description of Configuration 1"
    },
    {
      "name": "Configuration 2",
      "href": "/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/docgen/configurations/76543210-3210-3210-3210-109876543210",
      "id": "76543210-3210-3210-3210-109876543210",
      "description": "Description of Configuration 2"
    }
  ]
}
```

### Create DocLauncher Task

**Endpoint:** `/spring-api/v1/accounts/{accountId}/doclauncher/tasks`

**Method:** POST

**Description:** Creates a DocLauncher task.

**Path Parameters:**
- `accountId` (required): The DocuSign account ID

**Headers:**
- `Authorization` (required): Bearer {access_token}
- `Content-Type` (required): application/json

**Request Body:**
```json
{
  "configuration": {
    "href": "/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/docgen/configurations/87654321-4321-4321-4321-210987654321"
  },
  "parameters": "<xml>Your XML payload here</xml>"
}
```

**Example Request:**
```
POST https://clm.docusign.net/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/doclauncher/tasks
Authorization: Bearer eyJ0eXAi...
Content-Type: application/json

{
  "configuration": {
    "href": "/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/docgen/configurations/87654321-4321-4321-4321-210987654321"
  },
  "parameters": "<xml><customer><name>Acme Corp</name><address>123 Main St</address></customer></xml>"
}
```

**Response:**
```json
{
  "id": "65432109-2109-2109-2109-098765432109",
  "href": "/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/doclauncher/tasks/65432109-2109-2109-2109-098765432109",
  "resultUrl": "https://app-d.docusign.com/documents/details/65432109-2109-2109-2109-098765432109",
  "status": "completed"
}
```

### Get Document Attributes

**Endpoint:** `/spring-api/v1/accounts/{accountId}/documents/{documentId}/attributes`

**Method:** GET

**Description:** Retrieves attributes of a document.

**Path Parameters:**
- `accountId` (required): The DocuSign account ID
- `documentId` (required): The document ID

**Headers:**
- `Authorization` (required): Bearer {access_token}

**Example Request:**
```
GET https://clm.docusign.net/spring-api/v1/accounts/12345678-1234-1234-1234-123456789012/documents/65432109-2109-2109-2109-098765432109/attributes
Authorization: Bearer eyJ0eXAi...
```

**Response:**
```json
{
  "attributes": {
    "document": {
      "name": "Contract with Acme Corp",
      "status": "Draft",
      "createdDate": "2023-02-10T12:34:56Z",
      "createdBy": {
        "name": "John Doe",
        "email": "john.doe@example.com"
      },
      "metadata": {
        "contractValue": "100000",
        "contractTerm": "12 months",
        "customer": {
          "name": "Acme Corp",
          "address": "123 Main St",
          "contactPerson": "Jane Smith"
        }
      }
    }
  }
}
```

## Error Responses

### Authentication Errors

**Status Code:** 401 Unauthorized

**Response:**
```json
{
  "error": "invalid_grant",
  "error_description": "The authorization code is invalid or has expired."
}
```

### API Errors

**Status Code:** 400 Bad Request

**Response:**
```json
{
  "message": "Invalid request",
  "details": [
    {
      "field": "parameters",
      "message": "Invalid XML format"
    }
  ]
}
```

**Status Code:** 404 Not Found

**Response:**
```json
{
  "message": "Resource not found",
  "details": [
    {
      "field": "documentId",
      "message": "Document with ID 65432109-2109-2109-2109-098765432109 not found"
    }
  ]
}
```

**Status Code:** 500 Internal Server Error

**Response:**
```json
{
  "message": "Internal server error",
  "details": [
    {
      "message": "An unexpected error occurred"
    }
  ]
}
```

## Rate Limiting

DocuSign CLM API implements rate limiting to protect the service from excessive requests. When rate limits are exceeded, the API returns a 429 Too Many Requests status code.

**Status Code:** 429 Too Many Requests

**Response Headers:**
- `Retry-After`: The number of seconds to wait before making another request

**Response:**
```json
{
  "message": "Rate limit exceeded",
  "details": [
    {
      "message": "Too many requests, please try again after 60 seconds"
    }
  ]
}
```

## Best Practices

1. **Token Management**
   - Store refresh tokens securely
   - Implement token refresh logic
   - Check token validity before making API calls

2. **Error Handling**
   - Implement retry logic for transient errors
   - Handle rate limiting with exponential backoff
   - Provide user-friendly error messages

3. **Performance**
   - Cache DocGen configurations to reduce API calls
   - Implement pagination for large result sets
   - Use appropriate timeout values for API calls 