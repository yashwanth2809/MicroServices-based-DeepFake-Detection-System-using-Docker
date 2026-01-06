FROM python:3.10-slim

# 1) Set working directory to /app (so 'app' is on Python path)
WORKDIR /app

# 2) Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      curl && \
    rm -rf /var/lib/apt/lists/*

# 3) Tell Torch Hub to use /app/models for caching
ENV TORCH_HOME=/app/models

# 4) Prepare hub cache dirs (will be populated via volume mount)
RUN mkdir -p /app/models/hub/checkpoints

# 5) Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copy application code
COPY app/ ./app

# 7) Expose port
EXPOSE 8000

# 8) Start Uvicorn from the project root, pointing at app.main
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
