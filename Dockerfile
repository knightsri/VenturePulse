# VenturePulse v2 - AI-Powered Product Viability Analysis
# Docker image for the FastAPI web application

FROM python:3.11-slim

# Build arguments
ARG DOCKERUSER=venturepulse

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash ${DOCKERUSER}

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY prompts/ ./prompts/

# Create data directories and set ownership
RUN mkdir -p /app/data/reports /app/data/specs && \
    chown -R ${DOCKERUSER}:${DOCKERUSER} /app

# Switch to non-root user
USER ${DOCKERUSER}

# Default port (overridden by .env via docker-compose env_file)
ENV PORT=8080

# Health check using dynamic PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the FastAPI app with uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
