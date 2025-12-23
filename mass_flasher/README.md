# Mass Flasher Deployment on Raspberry Pi 5

## Prerequisites

- Generic Linux System (or Raspberry Pi) with Docker installed
- Docker installed
- Git installed
- Controlboard repository cloned

## Installation Steps

1. **Update Repository**:
   Navigate to the repository and pull the latest changes from the `dev` branch.

   ```bash
   cd ~/controlboard
   git checkout dev
   git pull origin dev
   ```

2. **Navigate to Mass Flasher Directory**:

   ```bash
   cd mass_flasher
   ```

3. **Make Script Executable** (if not already):

   ```bash
   chmod +x run_docker.sh
   ```

4. **Run the Application**:
   Execute the helper script to build and start the container.

   ```bash
   ./run_docker.sh
   ```

   This script will:
   - Build the `mass-flasher` Docker image.
   - Create a `config.json` file if it doesn't exist.
   - Stop and remove any existing container named `mass_flasher_app`.
   - Start a new container with auto-restart enabled.

5. **Access the Interface**:
   Open a web browser and navigate to:
   `http://<YOUR_RPI_IP>:5000`

## Troubleshooting

- **Logs**: To check the application logs, verify the container name (default: `mass_flasher_app`) and run:

  ```bash
  docker logs -f mass_flasher_app
  ```

- **Permissions**: Ensure your user is in the `docker` group to run docker commands without sudo:

  ```bash
  sudo usermod -aG docker $USER
  # Log out and back in for changes to take effect
  ```
