#!/bin/bash

# Create SSL directory if it doesn't exist
mkdir -p /app/ssl

# Generate SSL certificate and key
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /app/ssl/streamlit.key \
  -out /app/ssl/streamlit.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
chmod 600 /app/ssl/streamlit.key
chmod 600 /app/ssl/streamlit.crt

echo "SSL certificate generated successfully"
