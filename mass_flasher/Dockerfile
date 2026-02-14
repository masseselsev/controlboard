FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any needed for paramiko/cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY mass_flasher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mass_flasher/ .
COPY controlboard/dist/ /app/dist

# Create volume mount point for config
# Create volume mount point for data (config)
VOLUME /app/data

EXPOSE 5000

CMD ["python", "app.py"]
