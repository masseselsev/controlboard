#!/bin/bash

# Build the image
docker build -t mass-flasher .

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
  --name mass_flasher_app \
  --restart unless-stopped \
  mass-flasher

echo "Logs:"
docker logs -f mass_flasher_app
