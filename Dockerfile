FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Create default data directories
RUN mkdir -p /data/hermes_memory_engine/structural \
             /data/hermes_memory_engine/semantic/chroma_db

ENV PYTHONUNBUFFERED=1
ENV HERMES_CONFIG_PATH=/app/config.yaml

EXPOSE 8000

CMD ["python3", "-m", "pytest", "tests/", "-v"]
