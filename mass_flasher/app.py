from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, Response, jsonify, session, redirect, url_for, flash
from gevent.pywsgi import WSGIServer
from werkzeug.security import generate_password_hash, check_password_hash
import queue
import json
import os
import requests
from functools import wraps
from ssh_utils import FlashWorker, parse_ip_ranges

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_for_prod' 
log_queue = queue.Queue()

USERS_FILE = "data/users.json"
DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- USER MANAGEMENT ---

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- CONFIG MANAGEMENT ---

def get_config_path(username):
    return os.path.join(DATA_DIR, f"settings_{username}.json")

def load_user_config(username):
    path = get_config_path(username)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_config(username, config):
    path = get_config_path(username)
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)

# --- NOTIFICATIONS ---

def send_telegram_notification(ip, status, token, chat_id):
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

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        
        # Simple Admin init if no users exist
        if not users and username == 'admin':
            users['admin'] = generate_password_hash(password)
            save_users(users)
            session['user'] = 'admin'
            return redirect(url_for('index'))

        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    # Only allow logged in users to register new users? Or open registration?
    # For this task, let's allow open registration for invalid users OR simple management.
    # Let's simple allow registration if passed properly.
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
         return jsonify({"error": "Missing fields"}), 400
         
    users = load_users()
    if username in users:
        return jsonify({"error": "User exists"}), 400
        
    users[username] = generate_password_hash(password)
    save_users(users)
    return jsonify({"status": "created", "username": username})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session['user'])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    username = session['user']
    if request.method == 'POST':
        config = load_user_config(username)
        config['telegram_token'] = request.form.get('telegram_token')
        config['telegram_chat_id'] = request.form.get('telegram_chat_id')
        save_user_config(username, config)
        return jsonify({"status": "saved"})
    else:
        return jsonify(load_user_config(username))

@app.route('/flash', methods=['POST'])
@login_required
def flash_devices():
    username = session['user']
    data = request.json
    ip_string = data.get('ips', '')
    ssh_user = data.get('username', 'user')
    ssh_pass = data.get('password', 'admin')
    try:
        port = int(data.get('port', 2222))
    except ValueError:
        port = 2222
    
    ips = parse_ip_ranges(ip_string)
    
    if not ips:
        return jsonify({"error": "No valid IPs found"}), 400
        
    log_queue.put(f"[SYSTEM] User '{username}' starting batch for {len(ips)} devices.")
    
    config = load_user_config(username)
    tg_token = config.get("telegram_token", "")
    tg_chat_id = config.get("telegram_chat_id", "")

    # Create a closure to capture token/chat_id for THIS batch
    def notification_callback(ip, status):
        send_telegram_notification(ip, status, tg_token, tg_chat_id)

    for ip in ips:
        # Pass callback
        worker = FlashWorker(ip, ssh_user, ssh_pass, log_queue, port=port, 
                           completion_callback=notification_callback, 
                           tg_token=tg_token, tg_chat_id=tg_chat_id)
        worker.start()
        
    return jsonify({"status": "started", "count": len(ips)})

@app.route('/stream')
@login_required
def stream():
    def event_stream():
        while True:
            try:
                # Get log with timeout to allow checking for disconnects
                # Note: This shares the queue among ALL users.
                message = log_queue.get(timeout=10)
                yield f"data: {message}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    print("Serving on http://0.0.0.0:5000")
    http_server.serve_forever()
