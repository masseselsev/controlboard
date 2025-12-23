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
  --network host \
  -v "$(pwd)/config.json:/app/config.json" \
  -v "$(pwd)/docker_resolv.conf:/etc/resolv.conf" \
  --name mass_flasher_app \
  --restart unless-stopped \
  mass-flasher

echo "Logs:"
docker logs -f mass_flasher_app
