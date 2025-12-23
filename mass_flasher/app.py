from gevent import monkey
# Disable DNS patching to use system resolver (fixes NameResolutionError in some Docker/VPN setups)
monkey.patch_all(dns=False)

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
    
    # Suppress redundant notification if skipped? No, user wants ALL notifications.
    # if status == "SKIPPED":
    #     return

    # Debug log to verify callback execution
    log_queue.put(f"[{ip}] [DEBUG] Sending Telegram for status: {status}")

    if not token or not chat_id:
        log_queue.put(f"[{ip}] [WARN] Telegram config missing, notification skipped.")
        return

    if status == "SUCCESS":
        status_icon = "✅"
        action_text = "Firmware Update & Reboot"
    elif status == "SKIPPED":
        status_icon = "ℹ️"
        action_text = "Update Skipped (Already Checking)"
    else:
        status_icon = "❌"
        action_text = "Failed"

    status_text = status
    
    message = f"{status_icon} <b>Mass Flasher Report</b>\n\n" \
              f"<b>Target:</b> {ip}\n" \
              f"<b>Status:</b> {status_text}\n" \
              f"<b>Action:</b> {action_text}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
             log_queue.put(f"[{ip}] [ERROR] Telegram API Error {resp.status_code}: {resp.text}")
        else:
             log_queue.put(f"[{ip}] [INFO] Telegram notification sent.")
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
    
    for ip in ips:
        worker = FlashWorker(ip, username, password, log_queue, port=port, completion_callback=send_telegram_notification)
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

from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ssl
import socket

def generate_self_signed_cert():
    """Generates a self-signed certificate and key for HTTPS handling."""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"MassFlasher"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

class DualStackServer(WSGIServer):
    def handle(self, sock, address):
        try:
            # Peek at the first byte of the connection
            # TLS Client Hello always starts with 0x16
            first_byte = sock.recv(1, socket.MSG_PEEK)
            
            if len(first_byte) > 0 and first_byte[0] == 0x16:
                # This is an SSL/TLS connection.
                # Wrap the socket to accept the handshake, then redirect.
                self.handle_ssl_redirect(sock, address)
            else:
                # Standard HTTP connection, let WSGIServer handle it
                super().handle(sock, address)
        except Exception as e:
            # Log error but don't crash
            # print(f"Connection handling error: {e}")
            pass

    def handle_ssl_redirect(self, sock, address):
        try:
            # Context for our self-signed cert
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
            
            # Wrap the socket
            with context.wrap_socket(sock, server_side=True) as ssock:
                # Read the request line (we don't strictly need to parse it perfectly, 
                # but we need to consume it to satisfy the client usually)
                request_data = ssock.read(4096) 
                
                # Construct HTTP Redirect Response
                # We redirect to the same host but HTTP.
                # Since we don't easily know the full Host header from simple read without parsing,
                # we can try to extract it or just use a relative redirect if browser supports it (implied host).
                # But browsers need absolute URI usually for 301/302? No, location can be relative in modern HTTP.
                # However, switching protocol requires full URL.
                
                # Simple extraction of Host header
                decoded = request_data.decode('utf-8', errors='ignore')
                host = "localhost:5000" # Default
                for line in decoded.split('\r\n'):
                    if line.lower().startswith("host:"):
                        host = line.split(":", 1)[1].strip()
                        break
                
                redirect_url = f"http://{host}/"
                
                response = (
                    f"HTTP/1.1 302 Found\r\n"
                    f"Location: {redirect_url}\r\n"
                    f"Connection: close\r\n"
                    f"\r\n"
                )
                ssock.write(response.encode('utf-8'))
        except Exception as e:
            pass
            # print(f"SSL Redirect error: {e}")

if __name__ == '__main__':
    # Ensure certs exist for the redirector
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        print("Generating self-signed certificate for automatic HTTPS->HTTP redirect...")
        generate_self_signed_cert()

    # Disable the default log to stderr for WSGIServer to reduce noise? 
    # Or keep it. The DualStackServer should prevent the 'Invalid HTTP method' error reaching WSGI.
    http_server = DualStackServer(('0.0.0.0', 5000), app)
    print("Serving on http://0.0.0.0:5000 (with auto-redirect for HTTPS)")
    http_server.serve_forever()
