FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    xclip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create volume mount points for common directories
VOLUME ["/workspace", "/home/user/.claude"]

# Set environment variables with defaults
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m -s /bin/bash user
USER user

# Expose port for API
EXPOSE 8000

# Default command runs the API server
CMD ["python", "api/server.py"]