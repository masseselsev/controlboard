import os
import sys
import requests
import argparse

import subprocess
import re

SCRIPT_VERSION = "3"

def get_device_ip():
    try:
        cmd = "ip -4 addr show"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # 1. Try VPN IP (10.8.0.*)
        match_vpn = re.search(r'inet (10\.8\.0\.\d+)', result)
        if match_vpn:
            return match_vpn.group(1)
            
        # 2. Try Local IP (192.168.222.*)
        match_local = re.search(r'inet (192\.168\.222\.\d+)', result)
        if match_local:
            return match_local.group(1)
            
        # 3. Fallback: Get all global IPs (excluding loopback)
        # Find all inet addresses
        all_ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)
        valid_ips = [ip for ip in all_ips if not ip.startswith('127.')]
        
        if valid_ips:
            return ", ".join(valid_ips)
            
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
    ip_addr = get_device_ip()
    header = "<b>[VSM2 Flash&Control]</b>"
    final_message = f"{header}\n{message}\nDevice IP: {ip_addr}"

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
