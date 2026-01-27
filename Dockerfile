FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY setup.py README.md ./
COPY firstrade/ ./firstrade/

RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir fastapi uvicorn[standard]

# Copy server
COPY server.py ./

# Create directories for config and data
RUN mkdir -p /config /data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
