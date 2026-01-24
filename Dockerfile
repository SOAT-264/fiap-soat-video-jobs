FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8003

# Run application
CMD ["uvicorn", "job_service.infrastructure.adapters.input.api.main:app", "--host", "0.0.0.0", "--port", "8003"]
