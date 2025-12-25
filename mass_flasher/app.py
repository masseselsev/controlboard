from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, Response, jsonify
from gevent.pywsgi import WSGIServer
import queue
import json
import os
import requests
from ssh_utils import FlashWorker, parse_ip_ranges

app = Flask(__name__)
log_queue = queue.Queue()
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def send_telegram_notification(ip, status):
    config = load_config()
    token = config.get("telegram_token")
    chat_id = config.get("telegram_chat_id")
    
    # Suppress redundant notification if skipped (device already sent one)
    if status == "SKIPPED":
        return

    if not token or not chat_id:
        log_queue.put(f"[{ip}] [WARN] Telegram config missing, notification skipped.")
        return

    success = (status == "SUCCESS")
    status_icon = "✅" if success else "❌"
    status_text = status
    
    message = f"{status_icon} <b>Mass Flasher Report</b>\n\n" \
              f"<b>Target:</b> {ip}\n" \
              f"<b>Status:</b> {status_text}\n" \
              f"<b>Action:</b> Firmware Update & Reboot"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log_queue.put(f"[{ip}] [ERROR] Failed to send Telegram: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        config = load_config()
        config['telegram_token'] = request.form.get('telegram_token')
        config['telegram_chat_id'] = request.form.get('telegram_chat_id')
        save_config(config)
        return jsonify({"status": "saved"})
    else:
        return jsonify(load_config())

@app.route('/flash', methods=['POST'])
def flash_devices():
    data = request.json
    ip_string = data.get('ips', '')
    username = data.get('username', 'user')
    password = data.get('password', 'admin')
    try:
        port = int(data.get('port', 2222))
    except ValueError:
        port = 2222
    
    ips = parse_ip_ranges(ip_string)
    
    if not ips:
        return jsonify({"error": "No valid IPs found"}), 400
        
    log_queue.put(f"[SYSTEM] Starting batch for {len(ips)} devices: {', '.join(ips)} (Port: {port})")
    
    config = load_config()
    tg_token = config.get("telegram_token", "")
    tg_chat_id = config.get("telegram_chat_id", "")

    for ip in ips:
        worker = FlashWorker(ip, username, password, log_queue, port=port, completion_callback=send_telegram_notification, tg_token=tg_token, tg_chat_id=tg_chat_id)
        worker.start()
        
    return jsonify({"status": "started", "count": len(ips)})

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            try:
                # Get log with timeout to allow checking for disconnects
                message = log_queue.get(timeout=10)
                yield f"data: {message}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    print("Serving on http://0.0.0.0:5000")
    http_server.serve_forever()
