# ==========================================
# Dual-Purpose Dockerfile for AutoTailor
# ==========================================

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TESSDATA_PREFIX=/app/tessdata

# Install system dependencies (Tesseract, OpenGL, and glib for OpenCV headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml .

# Install dependencies and package in editable/development mode
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY . .

# Install web UI dependencies (Gradio)
RUN pip install --no-cache-dir gradio opencv-python-headless

# Expose the Gradio webserver port
EXPOSE 7860

# Define a default command (Runs Web app). Can be overridden via CLI args.
CMD ["python", "app.py"]
