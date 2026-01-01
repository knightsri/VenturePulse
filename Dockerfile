# VenturePulse - AI-Powered Product Viability Analysis
# Docker image for the Streamlit web application

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY prompts/ ./prompts/

# Create analyses directory
RUN mkdir -p /app/analyses

# Default port (can be overridden via PORT env var)
ARG PORT=8501
ENV PORT=${PORT}

# Expose the port
EXPOSE ${PORT}

# Set environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check (uses PORT env var at runtime)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Run the Streamlit app with port from environment
CMD streamlit run app/venturepulse.py --server.port=${PORT} --server.maxUploadSize=50
