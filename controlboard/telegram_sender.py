import os
import sys
import requests
import argparse

import subprocess
import re

SCRIPT_VERSION = "3"

def get_ip_section():
    try:
        cmd = "ip -4 addr show"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # Find all inet addresses
        all_ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)
        valid_ips = [ip for ip in all_ips if not ip.startswith('127.')]
        
        vpn_ips = [ip for ip in valid_ips if ip.startswith('10.8.0.')]
        local_ips = [ip for ip in valid_ips if ip.startswith('192.168.222.')]
        
        lines = []
        if vpn_ips:
            lines.append(f"VPN IP: {', '.join(vpn_ips)}")
        if local_ips:
            lines.append(f"Local IP: {', '.join(local_ips)}")
            
        # If neither specific category is found, fallback to listing all
        if not lines:
            if valid_ips:
                lines.append(f"IPs: {', '.join(valid_ips)}")
            else:
                lines.append("IPs: Unknown")
                
        return "\n".join(lines)
            
    except Exception as e:
        return f"IPs: Error ({e})"

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[INFO] Telegram credentials not found in environment. Skipping notification.")
        return

    # Append IP Address
    ip_section = get_ip_section()
    header = "<b>[VSM2 Flash&Control]</b>"
    final_message = f"{header}\n{message}\n{ip_section}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": final_message,
        "parse_mode": "HTML"
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
