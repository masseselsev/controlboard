#!/bin/bash

# Build the image
docker build -t mass-flasher .

# Run the container
# We mount a local config.json file (creating it if it doesn't exist) so settings persist.
touch config.json

echo "Starting Mass Flasher on http://localhost:5000"
docker run -d \
  -p 5000:5000 \
  -v "$(pwd)/config.json:/app/config.json" \
  --name mass_flasher_app \
  mass-flasher

echo "Logs:"
docker logs -f mass_flasher_app
