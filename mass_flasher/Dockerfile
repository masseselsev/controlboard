FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any needed for paramiko/cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create volume mount point for config
VOLUME /app/config.json

EXPOSE 5000

CMD ["python", "app.py"]
