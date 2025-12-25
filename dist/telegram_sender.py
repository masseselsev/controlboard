import os
import sys
import requests
import argparse

SCRIPT_VERSION = "1"

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[INFO] Telegram credentials not found in environment. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[INFO] Telegram notification sent successfully.")
        else:
            print(f"[WARN] Failed to send Telegram notification. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"[WARN] Error sending Telegram notification: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Telegram notification.")
    parser.add_argument("message", type=str, help="Message to send")
    args = parser.parse_args()

    send_telegram_message(args.message)
