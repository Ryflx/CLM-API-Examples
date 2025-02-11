#!/bin/bash

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Build the Docker image
echo "Building Docker image..."
docker-compose build

# Start the containers in detached mode
echo "Starting containers..."
docker-compose up -d

# Show the running containers
echo "Container status:"
docker-compose ps

echo "Application is running at http://localhost:8501"
