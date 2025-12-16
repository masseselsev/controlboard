# Walkthrough - Telegram Integration

I have added Telegram notification support to the firmware update process.

## Changes

### 1. New Script: `dist/telegram_sender.py`
A Python script that sends messages using the Telegram Bot API.
- Reads credentials (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) from environment variables.
- Fails gracefully if credentials are missing (prints an INFO message and exits).
- Uses `requests` to send the message.

### 2. Config Template: `dist/telegram_config.env`
A template file for storing your sensitive credentials.
```env
# Telegram Configuration
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Modified `dist/autoflash.sh` (v19)
- **Dependency**: Added `requests` to the pip install command.
- **Workflow**:
    1. Checks for `telegram_config.env`.
    2. Loads environment variables if the file exists.
    3. Constructs a message with the Hostname, Firmware Version, and Date.
    4. Calls `telegram_sender.py`.
    5. Version incremented to 19.

### 4. Versioning
- `autoflash.sh`: Updated to v19.
- `telegram_sender.py`: Initialized at v1.

## Verification Results
### Automated Verification
*Skipped as per user instructions.*

### Manual Verification Steps
To enable notifications:
1. Open `dist/telegram_config.env`.
2. Uncomment and fill in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
3. Run `dist/autoflash.sh` as usual.

If the config file is missing or empty, the script will proceed without errors, printing a log message about skipping the notification.
