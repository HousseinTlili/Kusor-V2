# backend/Dockerfile
# Multi-stage production container for KUSOR v3 Flask API

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (Tesseract OCR for French/Arabic, OpenCV libs, Curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . /app/backend

# Create uploads and temp directories
RUN mkdir -p /tmp/kusor_uploads /app/data

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/docs || exit 1

# Production WSGI server via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "180", "backend.app:app"]
