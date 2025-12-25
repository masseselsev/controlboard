# Mass Flasher Deployment with Docker Compose

## Prerequisites

- Generic Linux System (Ubuntu, Debian, Raspberry Pi OS, etc.)
- **Docker** & **Docker Compose** installed
- **Git** installed

## Quick Start (Fresh Install)

1. **Clone Repository**:
   Open a terminal and clone the repository.

   ```bash
   cd ~
   git clone https://github.com/masseselsev/controlboard.git
   cd controlboard
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
   - Create a persistent volume locally in `./data/`.
   - Start the container `mass_flasher_app`.

4. **Access the Interface**:
   Open a web browser and navigate to:
   **`http://<YOUR_DEVICE_IP>:5000`** 
   (e.g., `http://localhost:5000` or `http://192.168.1.50:5000`)

---

## Updating an Existing Installation

If you already have the repository cloned:

```bash
cd ~/controlboard
git checkout main
git pull origin main
cd mass_flasher
docker compose up -d --build
```

---

## Authentication & Users

The system uses a local user database.

1. **First Login / Admin Setup**:
   - Upon first access, you will be redirected to the **Login Page**.
   - Enter your desired **Admin Username** (e.g., `admin`) and **Password**.
   - Click **Login**.
   - **Important**: The first user to successfully login becomes the Admin (account is created automatically).

2. **Registering Additional Users**:
   - On the login page, enter a new Username and Password.
   - Click **Register**.
   - (Note: Currently registration is open; in a secured environment, you may want to restrict this or manage `data/users.json` manually).

3. **Logout**:
   - Use the **Logout** button in the header.

## Data Persistence

Configuration and user data are stored in the `./data` directory within `mass_flasher`.
- `data/users.json`: User credentials.
- `data/settings_<username>.json`: Per-user settings (Telegram tokens).

**Backups:** To backup your installation, simply copy the `mass_flasher/data/` folder.

## Usage

1. **Settings / Telegram**: 
   - Click **⚙️ Settings** to configure your **Telegram Bot Token** and **Chat ID**.
   - These settings are personal to your user account.
2. **Flash Parameters**: 
   - **Username/Password**: SSH credentials for the *target Raspberry Pi devices* (default: `user` / `admin`).
   - **SSH Port**: Default is `2222` (VSM2) or `22`.
3. **Targets**: 
   - Enter IP addresses or ranges (e.g., `192.168.1.10-20`).
4. **Start**: 
   - Click **Start Mass Flash**.

## Maintenance

**View Logs**:
```bash
docker compose logs -f
```

**Stop**:
```bash
docker compose down
```
