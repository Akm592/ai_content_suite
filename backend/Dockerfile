# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app/backend

# System dependencies:
# - build-essential: compile-time tools some wheels may need
# - libgl1-mesa-glx: common runtime dep for Pillow/OpenCV usage
# - tesseract-ocr: required binary for pytesseract OCR on Debian Bookworm
# - ffmpeg: required for pydub to process audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    tesseract-ocr \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Environment for FastAPI host/port
ENV HOST=0.0.0.0
ENV PORT=8000

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
