# DocuSign CLM API Examples

This application demonstrates the DocuSign CLM API integration capabilities, starting with DocLauncher Tasks. It provides a user-friendly interface for creating DocLauncher tasks and viewing their results.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your machine
  - This includes both Docker Engine and Docker Compose
  - For Linux users, you may need to [install Docker Compose separately](https://docs.docker.com/compose/install/)
- DocuSign Developer Account with CLM access
- DocuSign Integration Key (Client ID and Secret) with CLM API scopes

## Installation

### Windows/Mac
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

### Linux
1. Install Docker Engine:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. Install Docker Compose:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. Start Docker:
   ```bash
   sudo systemctl start docker
   ```

4. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

## Security and HTTPS

The application uses HTTPS with a self-signed certificate for secure local development:

1. SSL Certificate:
   - Generated automatically during Docker build
   - Valid for localhost only
   - Self-signed (you'll see a browser warning)
   - Located in the `ssl` directory

2. Browser Warning:
   - You'll see "Not secure" or similar warning
   - This is normal for self-signed certificates
   - Click "Advanced" and "Proceed" to continue
   - Only for local development use

3. HTTPS Configuration:
   - Application runs on https://localhost:8501
   - SSL certificate auto-generated
   - Secure communication enabled

## Testing with Docker

1. Clone this repository:
   ```bash
   git clone https://github.com/Ryflx/CLM-API-Examples.git
   cd CLM-API-Examples
   ```

2. Create required directories:
   ```bash
   mkdir -p .tokens logs src/image
   ```

3. Create a `.env` file in the root directory with your DocuSign credentials:
   ```env
   DOCUSIGN_CLIENT_ID=your_client_id
   DOCUSIGN_CLIENT_SECRET=your_client_secret
   DOCUSIGN_ACCOUNT_ID=your_account_id
   DOCUSIGN_AUTH_SERVER=account-d.docusign.com
   DOCUSIGN_OAUTH_BASE_URL=https://account-d.docusign.com/oauth
   DOCUSIGN_REDIRECT_URI=https://localhost:8501
   ```

4. You can run the application using either Docker Compose or Docker Run:

   **Option 1: Using Docker Compose:**
   ```bash
   # Build and start
   docker compose up --build
   
   # Or in background mode
   docker compose up --build -d
   ```

   **Option 2: Using Docker Run directly:**
   ```bash
   # Build the image
   docker build -t clm-api .

   # Run with explicit port publishing
   docker run -it \
     -p 8501:8501 \
     -v "$(pwd)/.tokens:/app/.tokens" \
     -v "$(pwd)/logs:/app/logs" \
     -v "$(pwd)/src/image:/app/image" \
     --env-file .env \
     clm-api
   ```

   The `-p 8501:8501` flag explicitly publishes the container's port 8501 to the host's port 8501. This is required for external access to the application.

5. The app will be available at:
   ```
   https://localhost:8501
   ```

6. To stop the app:
   ```bash
   docker-compose down
   ```

7. To view logs:
   ```bash
   docker-compose logs -f clm-app
   ```

8. To rebuild after changes:
   ```bash
   ./dockerbuild.sh
   ```

## Features

- OAuth2 authentication with DocuSign
- List and search DocLauncher configurations
- Create DocLauncher tasks with custom XML parameters
- View task results and status
- Comprehensive logging
- HTTPS with self-signed certificate

## Usage Instructions

1. **Authentication**:
   - Click "Connect to DocuSign" when you first open the app
   - Complete the OAuth flow in your browser
   - The app will maintain your authentication state

2. **Creating DocLauncher Tasks**:
   - Enter your DocuSign Account ID
   - Search and select a DocLauncher configuration
   - Enter your XML payload
   - Click "Create DocLauncher Task"
   - View the task result URL and status

## Port Configuration and Access

1. **Port Mapping**:
   The application inside the container runs on port 8501 and must be properly mapped to the host machine:
   ```bash
   # Verify correct port mapping in docker ps output
   docker ps
   # Should show: 0.0.0.0:8501->8501/tcp
   ```

   If you don't see this port mapping:
   ```bash
   # Stop any running containers
   docker compose down

   # Start with explicit port mapping
   docker compose up -d
   ```

2. **Verifying Container Access**:
   ```bash
   # Check if the application is binding correctly
   docker compose logs
   # Should show: "You can now view your Streamlit app in your browser."
   # and: "Network URL: http://0.0.0.0:8501"

   # Test connectivity (HTTP should redirect to HTTPS)
   curl -v http://localhost:8501
   
   # Test HTTPS (ignore SSL verification)
   curl -vk https://localhost:8501
   ```

3. **Common Access Issues**:
   - Use `localhost:8501` or `127.0.0.1:8501` in your browser
   - For external access, use the host machine's IP address
   - Check if port 8501 is already in use: `lsof -i :8501`
   
   **Firewall Checks:**
   
   Windows:
   ```bash
   # Check if port 8501 is blocked
   netsh advfirewall firewall show rule name=all | findstr "8501"
   
   # Temporarily disable firewall for testing (run as Administrator)
   netsh advfirewall set allprofiles state off
   
   # Don't forget to re-enable after testing
   netsh advfirewall set allprofiles state on
   ```
   
   macOS:
   ```bash
   # Check firewall status
   sudo defaults read /Library/Preferences/com.apple.alf globalstate
   
   # Temporarily disable firewall
   sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 0
   
   # Re-enable firewall after testing
   sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1
   ```
   
   Linux:
   ```bash
   # Check if port 8501 is allowed
   sudo ufw status | grep 8501
   
   # Allow port 8501 if needed
   sudo ufw allow 8501
   
   # Or temporarily disable firewall
   sudo ufw disable
   
   # Re-enable after testing
   sudo ufw enable
   ```

2. **Docker Issues**:
   - First, verify Docker Desktop is running
   - Check if the container is actually running:
     ```bash
     docker ps
     ```
     You should see a container with image 'clm-api-examples-clm-app' and port '0.0.0.0:8501->8501/tcp'
   
   - If you don't see the container, try these steps:
     ```bash
     # Stop any existing containers
     docker compose down

     # Remove old containers and images
     docker compose rm -f
     docker rmi clm-api-examples-clm-app

     # Rebuild and start (remove -d to see logs in real-time)
     docker compose up --build -d
     ```

   - To verify the container started properly:
     ```bash
     # Check container logs
     docker compose logs

     # You should see "You can now view your Streamlit app in your browser."
     # If you don't see this message, the container failed to start properly
     ```

2. **Authentication Issues**:
   - Verify your DocuSign credentials in `.env`
   - Ensure your Integration Key has CLM API scopes
   - Click "Disconnect" and try authenticating again

3. **Port Conflicts**:
   - If port 8501 is in use, modify the port mapping in `docker-compose.yml`:
     ```yaml
     ports:
       - "8502:8501"  # Change 8501 to any available port
     ```

4. **SSL Certificate Warning**:
   - Browser warning is normal for self-signed certificates
   - Click "Advanced" and "Proceed" to continue
   - Certificate is only for local development

## Logs

- Logs are stored in the `logs` directory
- They are persisted even when the container restarts
- Each day gets a new log file

## Security Notes

- Never commit your `.env` file
- Keep your DocuSign credentials secure
- The app stores authentication tokens in a volume mounted at `.tokens`
- HTTPS enabled with self-signed certificate for local security
- All communication between browser and app is encrypted

## Support

For issues or questions:
1. Check the logs in the `logs` directory
2. Refer to the [DocuSign CLM API Documentation](https://developers.docusign.com/docs/clm-api/)
3. Contact your DocuSign support representative

## Development

To modify the application:
1. Stop the containers: `docker-compose down`
2. Make your changes
3. Rebuild and start: `docker-compose up --build`

## Deployment to Streamlit Community Cloud

1. Fork this repository to your GitHub account

2. Create a `.streamlit/secrets.toml` file locally with your DocuSign credentials:
   ```toml
   # DocuSign API Configuration
   DOCUSIGN_CLIENT_ID = "your_client_id"
   DOCUSIGN_CLIENT_SECRET = "your_client_secret"
   DOCUSIGN_ACCOUNT_ID = "your_account_id"
   DOCUSIGN_AUTH_SERVER = "account-d.docusign.com"
   DOCUSIGN_OAUTH_BASE_URL = "https://account-d.docusign.com/oauth"
   DOCUSIGN_REDIRECT_URI = "https://localhost:8501"
   ```

3. Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your forked repository
   - Select the main branch
   - Set the path to `src/app.py`

4. Add your secrets in Streamlit Cloud:
   - In your deployed app settings
   - Go to "Secrets"
   - Paste the contents of your `secrets.toml` file
   - Update `DOCUSIGN_REDIRECT_URI` to match your Streamlit Cloud URL

5. The app will automatically deploy and be available at your Streamlit Cloud URL

Note: When deploying to Streamlit Cloud:
- The app will use `secrets.toml` instead of `.env`
- Update your DocuSign redirect URI in both Streamlit secrets and DocuSign app settings
- Make sure your DocuSign integration key has the correct redirect URI
