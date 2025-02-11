FROM python:3.12-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && \
    apt-get install -y openssl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p .tokens logs ssl

# Generate SSL certificate
COPY ssl/generate_cert.sh /app/ssl/
RUN chmod +x /app/ssl/generate_cert.sh && \
    /app/ssl/generate_cert.sh

# Expose Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "src/app.py", "--server.address", "0.0.0.0"]
