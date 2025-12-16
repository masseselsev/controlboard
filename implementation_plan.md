# Implementation Plan - Telegram Notifications

## Goal Description
Add functionality to send a Telegram notification upon successful firmware flashing completion using `autoflash.sh`.

## User Review Required
> [!IMPORTANT]
> **Configuration**: You must provide your `BOT_TOKEN` and `CHAT_ID` in `dist/telegram_config.env` (file will be created).

## Proposed Changes
### [NEW] [telegram_sender.py](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/telegram_sender.py)
- A script that reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment variables.
- Sends a text message passed as an argument.
- Uses `requests` library.

### [NEW] [telegram_config.env](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/telegram_config.env)
- Key-value pairs for configuration.
- `TELEGRAM_BOT_TOKEN=`
- `TELEGRAM_CHAT_ID=`

### [MODIFY] [autoflash.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/autoflash.sh)
- **Step 2**: Install `requests` in the python virtual environment.
- **Step 7**: Source `telegram_config.env` (if exists) and call `telegram_sender.py` with version info.

## Verification Plan
### Manual Verification
- **Run Sender Manually**:
  ```bash
  cd dist
  source env/bin/activate
  export TELEGRAM_BOT_TOKEN="your_token"
  export TELEGRAM_CHAT_ID="your_id"
  python telegram_sender.py "Test message from CLI"
  ```
- **Run Autoflash**:
  - Perform a flash sequence.
  - Verify message arrives in Telegram.
