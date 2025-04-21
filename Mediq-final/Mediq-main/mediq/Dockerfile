FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project
COPY . .

# Create directories
RUN mkdir -p /app/static /app/media /app/accounts/static

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Run server
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"] 