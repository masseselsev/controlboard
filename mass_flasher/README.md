# Mass Flasher Deployment with Docker Compose

## Prerequisites

- Generic Linux System (or Raspberry Pi)
- Docker & Docker Compose installed
- Git installed
- Controlboard repository cloned

## Quick Start (Docker Compose)

1. **Clone/Update Repository**:
   Navigate to the repository and pull the latest changes from the `main` branch.

   ```bash
   cd ~/controlboard
   git checkout main
   git pull origin main
   ```

2. **Navigate to Mass Flasher Directory**:

   ```bash
   cd mass_flasher
   ```

3. **Start the Application**:
   Use Docker Compose to build and start the service in background mode.

   ```bash
   # New Docker Compose V2
   docker compose up -d --build
   
   # Or legacy docker-compose
   docker-compose up -d --build
   ```

   This will:
   - Build the `mass-flasher` Docker image.
   - Create a persistent volume in `./data/` for storing users and configurations.
   - Start the container `mass_flasher_app` on host network (or mapping port 5000).

4. **Access the Interface**:
   Open a web browser and navigate to:
   **`http://<YOUR_IP>:5000`** (e.g. http://localhost:5000)

## Authentication & Users

The system now supports user authentication.

1. **First Login / Admin Setup**:
   - Upon first access, you will be redirected to the **Login Page**.
   - Enter your desired **Username** (e.g., `admin`) and **Password**.
   - Click **Login**.
   - Since no users exist initially, the first login attempt with the username `admin` will **automatically create the Admin account** with the password you provided.

2. **Registering Additional Users**:
   - On the login page, enter a new Username and Password.
   - Click **Register**.
   - Alternatively, logged-in users can just share creds, or you can manage `data/users.json` manually if needed.

3. **Logout**:
   - Use the **Logout** button in the header to end your session.

## Data Persistence

Configuration and user data are stored in the `./data` directory within `mass_flasher`. This directory is mounted into the container.
- `data/users.json`: Stores user credentials (hashed).
- `data/settings_<username>.json`: Stores per-user settings (e.g., Telegram tokens).

**Backups:** You only need to backup the `data/` folder.

## Usage

1. **Settings / Telegram**: 
   - Click **⚙️ Settings** to configure your Telegram Bot Token and Chat ID.
   - These settings are **specific to your user account**.
2. **Flash Parameters**: 
   - **Username/Password**: Enter the SSH credentials for the target devices (default: `user` / `admin`).
   - **SSH Port**: Default is `2222` (for recent VSM2 versions) or `22`.
3. **Targets**: 
   - Enter IP addresses or ranges (e.g., `192.168.1.10-20`).
4. **Start**: 
   - Click **Start Mass Flash**.Logs will appear in real-time tabs.

## Maintenance

**View Logs**:
```bash
docker compose logs -f
```

**Restart/Update**:
```bash
git pull origin main
docker compose up -d --build
```

**Stop**:
```bash
docker compose down
```
