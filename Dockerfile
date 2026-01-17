FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ron \
    poppler-utils \
    libglib2.0-0 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run.py .
COPY migrations/ ./migrations/

# Create necessary directories with proper permissions
RUN mkdir -p data uploads instance && \
    chmod 755 data uploads instance

# Expose port
EXPOSE 5103

# Run the application with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5103", "--workers", "2", "--threads", "4", "run:app"]
