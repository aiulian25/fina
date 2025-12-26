FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run.py .

# Create necessary directories with proper permissions
RUN mkdir -p data uploads instance && \
    chmod 755 data uploads instance

# Expose port
EXPOSE 5103

# Run the application
CMD ["python", "run.py"]
