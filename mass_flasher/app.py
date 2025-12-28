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

def send_telegram_notification(ip, status, token, chat_id, error_detail=None):
    # Suppress redundant notification if skipped (device already sent one)
    # User requested ONLY errors from web app. Success/Skipped are handled by script.
    if status in ["SUCCESS", "SKIPPED"]:
        return

    if not token or not chat_id:
        log_queue.put(f"[{ip}] [WARN] Telegram config missing, notification skipped.")
        return

    success = (status == "SUCCESS")
    status_icon = "✅" if success else "❌"
    
    status_map = {
        "SUCCESS": "УСПЕХ",
        "FAILURE": "СБОЙ",
        "SKIPPED": "ПРОПУЩЕНО"
    }
    status_text = status_map.get(status, status)
    
    message = f"{status_icon} <b>Отчет Mass Flasher</b>\n\n" \
              f"<b>Устройство:</b> {ip}\n" \
              f"<b>Статус:</b> {status_text}\n"

    if error_detail:
        message += f"<b>Ошибка:</b> {error_detail}\n"

    message += f"<b>Действие:</b> Обновление прошивки и перезагрузка"

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
        
        if request.is_json:
            # Merge JSON data (e.g. quick_actions)
            config.update(request.json)
        else:
            # Handle Form Data (Legacy/Telegram Settings Modal)
            if request.form.get('telegram_token') is not None:
                config['telegram_token'] = request.form.get('telegram_token')
            if request.form.get('telegram_chat_id') is not None:
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
    def notification_callback(ip, status, error_detail=None):
        send_telegram_notification(ip, status, tg_token, tg_chat_id, error_detail)

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

import subprocess
import glob
import sys

# Add dist to sys.path to import commands definition for autocomplete
sys.path.append(os.path.join(os.path.dirname(__file__), 'dist'))
# Also add local development path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'controlboard', 'dist')))

# Try to import commands, handle failure if dist not present yet (during build/dev)
try:
    import commands
except ImportError:
    commands = None



# --- CONSOLE API ---

@app.route('/api/console/ports')
@login_required
def get_console_ports():
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    # fallback for testing if no hardware
    if not ports:
        ports = ['/dev/ttyUSB0 (Simulated)']
    return jsonify(ports)

@app.route('/api/console/commands')
@login_required
def get_console_commands():
    if not commands:
        return jsonify([])
    cmds = []
    
    def add_cmds(array, type_name):
        for name, data in array.items():
            cmds.append({
                "value": f"{type_name} {name}", 
                "label": f"{name} ({type_name})", 
                "desc": data.get("description", "")
            })

    # Available arrays in commands.py
    if hasattr(commands, 'cmd_read_array'): add_cmds(commands.cmd_read_array, 'read')
    if hasattr(commands, 'cmd_write_array'): add_cmds(commands.cmd_write_array, 'write')
    if hasattr(commands, 'cmd_control_array'): add_cmds(commands.cmd_control_array, 'control')
    if hasattr(commands, 'cmd_test_array'): add_cmds(commands.cmd_test_array, 'test')
    if hasattr(commands, 'cmd_util_array'): add_cmds(commands.cmd_util_array, 'util')
    
    return jsonify(cmds)

# --- CONSOLE SESSIONS ---
CONSOLE_SESSIONS = {}

@app.route('/api/console/connect', methods=['POST'])
@login_required
def console_connect():
    username = session['user']
    data = request.json
    target_ip = data.get('ip', '').strip()
    ssh_port = int(data.get('ssh_port', 2222))
    ssh_user = data.get('username', 'user')
    ssh_pass = data.get('password', '12341234')
    
    if not target_ip:
        return jsonify({"error": "No Target IP provided"}), 400

    # Clean up existing session if any
    if username in CONSOLE_SESSIONS:
        try:
            CONSOLE_SESSIONS[username].close()
        except:
            pass
        del CONSOLE_SESSIONS[username]

    import paramiko
    import time

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(target_ip, port=ssh_port, username=ssh_user, password=ssh_pass, timeout=15)

        # 1. Check/Deploy Tools
        # Check if ~/controlboard/app.py exists
        stdin, stdout, stderr = ssh.exec_command("test -f ~/controlboard/app.py && echo 'FOUND' || echo 'MISSING'")
        status = stdout.read().decode().strip()
        
        if status == 'MISSING':
            # Auto-Deploy from local dist/
            # We assume local /app/dist is available (mounted in Docker)
            local_dist = "/app/dist"
            if not os.path.exists(local_dist):
                # Fallback if running outside docker or path diff
                local_dist = "dist" 
            
            # Send status update (Need a way to send partial output? 
            # We are inside the connect request, we can't stream yet. 
            # We'll just do it and return result log.)
            
            # Send status update via SSE for real-time feedback
            boot_logs = []
            def log_boot(msg):
                boot_logs.append(msg)
                # Stream to frontend via SSE
                timestamp = time.strftime("%H:%M:%S")
                log_queue.put(f"[{timestamp}] [{target_ip}] {msg}")

            sftp = ssh.open_sftp()
            try:
                ssh.exec_command("mkdir -p ~/controlboard")
                
                # Upload Files
                files_to_deploy = ['app.py', 'commands.py', 'controlboard.py']
                for fname in files_to_deploy:
                    local_path = os.path.join(local_dist, fname)
                    remote_path = f"controlboard/{fname}" # relative to home
                    if os.path.exists(local_path):
                        sftp.put(local_path, remote_path)
                
                # Check dependencies (pyserial) in venv or system?
                # The user insists on following setup.sh which uses venv.
                # So we should try to set up venv if possible.
                
                # Check if venv exists
                stdin, stdout, stderr = ssh.exec_command("test -f ~/controlboard/env/bin/python3 && echo 'FOUND' || echo 'MISSING'")
                venv_status = stdout.read().decode().strip()
                
                if venv_status == 'MISSING':
                    log_boot("[System] Creating virtual environment (env)...")
                    # Create venv
                    # Try to create. If it fails, install python3-venv
                    _, stdout, stderr = ssh.exec_command("cd ~/controlboard && python3 -m venv env")
                    exit_code = stdout.channel.recv_exit_status()
                    
                    if exit_code != 0:
                        err_out = stderr.read().decode().strip()
                        log_boot(f"[ERROR] venv creation failed: {err_out}. Installing python3-venv...")
                        # Failed, likely missing venv package
                        # We use sudo non-interactive
                        install_cmd = f"echo '{ssh_pass}' | sudo -S apt-get update && echo '{ssh_pass}' | sudo -S apt-get install -y python3-venv"
                        _, i_out, i_err = ssh.exec_command(install_cmd)
                        result_log = i_out.read().decode() + i_err.read().decode()
                        log_boot(f"[System] Setup log: {result_log[:200]}...") # truncate
                        
                        # Retry create
                        _, stdout, stderr = ssh.exec_command("cd ~/controlboard && python3 -m venv env")
                        exit_code = stdout.channel.recv_exit_status()
                        if exit_code != 0:
                            log_boot(f"[ERROR] venv retry failed: {stderr.read().decode().strip()}")
                        else:
                            log_boot("[System] venv created successfully.")
                    
                    # Install deps
                    log_boot("[System] Installing dependencies (pyserial, requests)...")
                    _, i_out, i_err = ssh.exec_command("cd ~/controlboard && ./env/bin/pip install pyserial requests")
                    
                    pip_exit = i_out.channel.recv_exit_status()
                    pip_out = i_out.read().decode().strip()
                    pip_err = i_err.read().decode().strip()
                    
                    if pip_exit != 0:
                        log_boot(f"[ERROR] pip install failed: {pip_out} {pip_err}")
                    else:
                         log_boot(f"[System] pip installed: {pip_out}")
                else:
                    # Check deps
                    stdin, stdout, stderr = ssh.exec_command("~/controlboard/env/bin/python3 -c 'import serial; import requests' 2>/dev/null && echo 'OK' || echo 'MISSING'")
                    if stdout.read().decode().strip() == 'MISSING':
                         log_boot("[System] Installing missing dependencies...")
                         _, i_out, i_err = ssh.exec_command("cd ~/controlboard && ./env/bin/pip install pyserial requests")
                         pip_out = i_out.read().decode().strip()
                         pip_err = i_err.read().decode().strip()
                         if pip_err:
                             log_boot(f"Output: {pip_out}\nErrors: {pip_err}")
                         else:
                             log_boot(pip_out)
                    
            except Exception as e:
                return jsonify({"error": f"Bootstrap failed: {str(e)}"}), 500
            finally:
                sftp.close()

        # 1.5. Ensure Permissions (dialout)
        # Check current groups
        stdin, stdout, stderr = ssh.exec_command("groups")
        groups_str = stdout.read().decode().strip()
        
        if "dialout" not in groups_str:
            # Add user to dialout
            print(f"[DEBUG] Adding user {ssh_user} to dialout group")
            add_group_cmd = f"echo '{ssh_pass}' | sudo -S usermod -aG dialout {ssh_user}"
            ssh.exec_command(add_group_cmd)
        
        # We use 'sg dialout' to force group usage usage without relogin
        # Prefix for commands needing serial access
        sg_prefix = "sg dialout -c "
        
        # PYTHON INTERPRETER TO USE
        # We prefer the venv path
        python_bin = "~/controlboard/env/bin/python3"
        # Check integrity
        stdin, stdout, stderr = ssh.exec_command(f"test -f {python_bin} && echo 'VENV' || echo 'SYS'")
        if stdout.read().decode().strip() == 'SYS':
            python_bin = "python3"

        # 2. Smart Port Detection & Version Check
        target_port = "/dev/ttyUSB0" # fallback
        detected_ver = "Unknown"
        port_input = data.get('port', '').strip()
        
        if port_input:
            target_port = port_input
        else:
            # Get list of ports
            stdin, stdout, stderr = ssh.exec_command("ls /dev/ttyUSB* 2>/dev/null")
            ports_str = stdout.read().decode().strip()
            # If empty, try ACM
            if not ports_str:
                 stdin, stdout, stderr = ssh.exec_command("ls /dev/ttyACM* 2>/dev/null")
                 ports_str = stdout.read().decode().strip()
            
            candidates = ports_str.split()
            found_active = False
            
            debug_errors = []
            for port in candidates:
                # Run tech_data check
                check_cmd = f"{sg_prefix} 'cd ~/controlboard && timeout 5s {python_bin} -u dist/controlboard.py read tech_data -p {port}'"
                
                stdin, stdout, stderr = ssh.exec_command(check_cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                
                if "Update Version:" in out:
                    target_port = port
                    # Extract Version
                    import re
                    m = re.search(r"Update Version:\s*([\d\.]+)", out)
                    if m:
                        detected_ver = f"V{m.group(1)}"
                    found_active = True
                    break
                else:
                    debug_errors.append(f"{port}: {out} | {err}")
            
            if not found_active and candidates:
                target_port = candidates[0]

        # Start interactive shell
        channel = ssh.invoke_shell()
        channel.settimeout(3.0)
        
        # Start the REPL app
        channel.send(f"{sg_prefix} 'cd ~/controlboard && {python_bin} -u app.py'\n")
        
        # Helper to wait for string
        def wait_and_send(pattern, send_str):
            buff = ""
            start_t = time.time()
            while time.time() - start_t < 8: # Increased timeout
                if channel.recv_ready():
                    chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                    buff += chunk
                    if pattern in buff:
                        channel.send(send_str + "\n")
                        return True, buff
                else:
                    time.sleep(0.1)
            return False, buff

        import time
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        # 3. Wait for Port prompt
        ok, log1 = wait_and_send("Введите COM-порт", target_port)
        
        # 4. Wait for Baud prompt
        ok, log2 = wait_and_send("Введите baudrate", "19200")
        
        # 5. Wait for Startup Complete (Ready state)
        # We wait for "[OK]" or output to stabilize
        log3 = ""
        start_t = time.time()
        while time.time() - start_t < 3:
             if channel.recv_ready():
                 chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                 log3 += chunk
                 if "Порт" in chunk or "[OK]" in chunk or "help" in chunk:
                     break
             else:
                 time.sleep(0.1)
        
        # 6. Read any remaining buffer
        output = log1 + log2 + log3
        while channel.recv_ready():
            output += channel.recv(1024).decode('utf-8', errors='ignore')

        # Clean ANSI artifacts like [?2004h
        clean_output = ansi_escape.sub('', output)
            
        CONSOLE_SESSIONS[username] = channel
        
        scan_msg = ""
        if not port_input:
             if found_active:
                 scan_msg = f"[System] Auto-Detected Controller on {target_port} ({detected_ver}) [Py: {python_bin}]\n"
             else:
                 error_details = "; ".join(debug_errors)
                 scan_msg = f"[System] Scan failed to find active controller. Using {target_port}. (Debug: {error_details})\n"

        init_msg = ""
        if status == 'MISSING':
            init_msg += "[System] Bootstrap verification complete.\n"
            
        return jsonify({"status": "connected", "output": init_msg + scan_msg + clean_output})

    except Exception as e:
        return jsonify({"error": f"Connection failed: {str(e)}"}), 500

@app.route('/api/console/send', methods=['POST'])
@login_required
def console_send():
    username = session['user']
    if username not in CONSOLE_SESSIONS:
        return jsonify({"error": "Not connected"}), 400
        
    channel = CONSOLE_SESSIONS[username]
    data = request.json
    cmd = data.get('cmd', '')
    
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    try:
        if cmd:
            channel.send(cmd + "\n")
            
        # Read output
        import time
        time.sleep(0.5) # Wait for processing
        output = ""
        attempts = 0
        while attempts < 10:
            if channel.recv_ready():
                output += channel.recv(4096).decode('utf-8', errors='ignore')
                attempts = 0 # reset if we got data
            else:
                time.sleep(0.1)
                attempts += 1
        
        clean_output = ansi_escape.sub('', output)
        return jsonify({"output": clean_output})
    except Exception as e:
        del CONSOLE_SESSIONS[username]
        return jsonify({"error": f"Session Lost: {str(e)}"}), 500





@app.route('/api/console/disconnect', methods=['POST'])
@login_required
def console_disconnect():
    username = session['user']
    if username in CONSOLE_SESSIONS:
        try:
            CONSOLE_SESSIONS[username].close()
        except:
            pass
        del CONSOLE_SESSIONS[username]
    return jsonify({"status": "disconnected"})



if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    print("Serving on http://0.0.0.0:5000")
    http_server.serve_forever()
