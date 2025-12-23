#!/bin/bash

# Ensure we are in the script's directory (where Dockerfile is)
cd "$(dirname "$0")"

# Build the image (force rebuild to pick up code changes)
# Explicitly remove old image if it exists to be safe
if [ "$(docker images -q mass-flasher)" ]; then
    docker rmi mass-flasher || true
fi

docker build --no-cache -t mass-flasher .

# Run the container
# We mount a local config.json file (creating it if it doesn't exist) so settings persist.
touch config.json

# Clean up existing container
if [ "$(docker ps -aq -f name=mass_flasher_app)" ]; then
    echo "Stopping and removing existing container..."
    docker rm -f mass_flasher_app
fi

echo "Starting Mass Flasher on http://localhost:5000"
docker run -d \
  -p 5000:5000 \
  --dns 8.8.8.8 \
  --dns 1.1.1.1 \
  -v "$(pwd)/config.json:/app/config.json" \
  --name mass_flasher_app \
  --restart unless-stopped \
  mass-flasher

echo "Logs:"
docker logs -f mass_flasher_app
