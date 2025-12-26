import os
import sys
import requests
import argparse

import subprocess
import re

SCRIPT_VERSION = "2"

def get_vpn_ip():
    try:
        # User requested IP from 'ip a' matching 10.8.0.*
        cmd = "ip -4 addr show"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # Look for 10.8.0.x
        # inet 10.8.0.93/24 scope global tun0
        match = re.search(r'inet (10\.8\.0\.\d+)', result)
        if match:
            return match.group(1)
    except Exception as e:
        return f"Unknown (Error: {e})"
    return "Unknown"

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[INFO] Telegram credentials not found in environment. Skipping notification.")
        return

    # Append IP Address
    vpn_ip = get_vpn_ip()
    final_message = f"{message}\nVPN IP: {vpn_ip}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": final_message
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
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
