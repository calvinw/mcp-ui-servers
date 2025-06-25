FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the unified server and subdirectories
COPY unified_sse_server.py .
COPY mcp-strudel/ ./mcp-strudel/
COPY mcp-button-state/ ./mcp-button-state/

# Expose port for the unified proxy server
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Start script to run all three servers
COPY start_servers.sh .
RUN chmod +x start_servers.sh

# Run the start script
CMD ["./start_servers.sh"]