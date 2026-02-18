import paramiko
import threading
import time
import socket
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def clean_ansi(text):
    # Aggressively remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Remove other control chars like \a (bell) etc, but keep \n
    text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f]', '', text) 
    return text.strip()

def get_source_ip(target_ip, port=22):
    """Determines the source IP that would be used to connect to the target."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target_ip, port))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

class FlashWorker(threading.Thread):
    def __init__(self, ip, username, password, log_queue, port=22, completion_callback=None, tg_token="", tg_chat_id="", advertised_ip=None, timezone="UTC"):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.log_queue = log_queue
        self.completion_callback = completion_callback
        self.tg_token = tg_token
        self.tg_chat_id = tg_chat_id
        self.advertised_ip = advertised_ip
        self.timezone = timezone
        self.status = "FAILURE" # SUCCESS, SKIPPED, FAILURE
        self.last_log_line = ""

    def log(self, message):
        try:
            # Handle potential invalid timezone strings gracefully
            tz = ZoneInfo(self.timezone) if self.timezone else None
        except Exception:
            tz = None
            
        if tz:
            timestamp = datetime.now(tz).strftime("%H:%M:%S")
        else:
            # Fallback to system local time if TZ invalid or not set
            timestamp = time.strftime("%H:%M:%S")
            
        formatted = f"[{timestamp}] [{self.ip}] {message}"
        self.log_queue.put(formatted)

    def run(self):
        self.log("Connecting...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        reboot_triggered = False

        try:
            client.connect(self.ip, port=self.port, username=self.username, password=self.password, timeout=10)
            self.log("Connected. Starting flash process...")
            
            # Construct the command
            # We use the raw file URL logic similar to setup.sh but ensure it executes non-interactively
            # Note: We need to point to the correct validation/setup script
            # For this task, we assume the standard setup.sh URL which we modified to accept --flash-reboot
            # We use 'dev' branch as requested.
            # Inject Telegram credentials so the script can send rich notifications
            if not self.tg_token or not self.tg_chat_id:
                self.log("WARN: Telegram credentials are missing. Notifications will NOT be sent.")
            
            # Determine BASE_URL for offline/local flashing
            source_ip = get_source_ip(self.ip, self.port)
            base_url_env = ""
            
            # Priority 1: Explicitly Advertised IP (e.g. from Host Header) -> Fixes Docker
            if self.advertised_ip:
                base_url = f"http://{self.advertised_ip}:5000"
                base_url_env = f'export BASE_URL="{base_url}"; '
                self.log(f"Using Advertised Flasher URL: {base_url}")
            # Priority 2: Detected Local IP (Backup, works for local non-docker)
            elif source_ip:
                # We assume the flask app is running on port 5000 on the same interface
                base_url = f"http://{source_ip}:5000"
                base_url_env = f'export BASE_URL="{base_url}"; '
                self.log(f"Using Detected Local Flasher URL: {base_url}")
            
            env_vars = f'export TELEGRAM_BOT_TOKEN="{self.tg_token}"; export TELEGRAM_CHAT_ID="{self.tg_chat_id}"; export TERM=xterm-256color; {base_url_env}'
            # Fix CRLF issues by stripping \r with tr or sed
            # wget -q -O - "..." | tr -d '\r' | bash -s "..." --flash-cleanup
            
            # If BASE_URL is set, we use it to fetch setup.sh, otherwise GitHub
            # We construct a primary URL command
            if base_url_env:
                 # Local Setup URL
                 setup_url = f"{base_url}/files/controlboard/setup.sh"
                 # We pass the setup_url as argument so the script knows where it came from (logic in setup.sh)
                 # ADDED TIMEOUT --timeout=10 to prevent hanging
                 cmd = env_vars + f'mkdir -p ~/controlboard; if wget --timeout=10 -q -O ~/controlboard/setup.sh "{setup_url}"; then chmod +x ~/controlboard/setup.sh; ~/controlboard/setup.sh "{setup_url}" --flash-cleanup; else echo "Error: Failed to download setup.sh from {setup_url}"; exit 1; fi'
            else:
                 # Fallback to GitHub
                 cmd = env_vars + 'mkdir -p ~/controlboard; url="https://raw.githubusercontent.com/masseselsev/controlboard/main/controlboard/setup.sh?v=$(date +%s)"; if wget --timeout=10 -q -O ~/controlboard/setup.sh "$url"; then chmod +x ~/controlboard/setup.sh; ~/controlboard/setup.sh "$url" --flash-cleanup; else echo "Error: Failed to download setup.sh"; exit 1; fi'
            
            # Execute
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            
            # Stream output with support for \r (progress bars)
            channel = stdout.channel
            buffer = ""
            
            # Filter verbose junk to prevent SSH buffer stall / device timeout
            JUNK_PATTERNS = ["Got byte", "Send byte", "Index finish", "Sent 'run'", "Sent 'yes'", "byte:", "Detected version:", "Trying send", "Start address"]
            
            while not channel.exit_status_ready() or channel.recv_ready():
                if channel.recv_ready():
                    data = channel.recv(4096).decode('utf-8', errors='replace')
                    
                    # Pre-filter large chunks if possible or process line by line
                    # Since data can be partial, we add to buffer then split
                    buffer += data
                    
                    while '\n' in buffer or '\r' in buffer:
                        idx_n = buffer.find('\n')
                        idx_r = buffer.find('\r')
                        
                        # Find nearest separator
                        if idx_n != -1 and (idx_r == -1 or idx_n < idx_r):
                            line = buffer[:idx_n]
                            buffer = buffer[idx_n+1:]
                            # Filter
                            clean_content = clean_ansi(line) # now returns stripped
                            
                            # Check for success indicators before filtering
                            if "The system will reboot now" in clean_content or "Перезагрузка..." in clean_content:
                                reboot_triggered = True

                            if clean_content and \
                               not any(x in line for x in JUNK_PATTERNS) and \
                               not clean_content.startswith("Hit:") and \
                               not clean_content.startswith("Get:") and \
                               not re.match(r'^[\d\s]+$', clean_content): # Skip lines with only numbers/spaces
                               
                                # Additional debug filter
                                if clean_content.startswith(">") and "progress" not in clean_content.lower():
                                    pass 
                                else:
                                    self.log(clean_content)

                        elif idx_r != -1:
                            line = buffer[:idx_r]
                            # Keep \r for progress bars if valid
                            buffer = buffer[idx_r+1:]
                            clean_content = clean_ansi(line)
                            
                            # Check for success indicators
                            if "The system will reboot now" in clean_content or "Перезагрузка..." in clean_content:
                                reboot_triggered = True

                            if ("progress:" in line or "Working" in line or "%" in line) and clean_content:
                                self.log(clean_content + "\r")
                            elif clean_content and \
                                 not any(x in line for x in JUNK_PATTERNS) and \
                                 not clean_content.startswith("Hit:") and \
                                 not clean_content.startswith("Get:") and \
                                 not re.match(r'^[\d\s]+$', clean_content):
                                 
                                if clean_content.startswith(">") and "progress" not in clean_content.lower():
                                    pass
                                else:
                                    self.log(clean_content)
                else:
                    time.sleep(0.01)

            # Flush
            buffer_clean = clean_ansi(buffer)
            if buffer_clean and not any(x in buffer for x in JUNK_PATTERNS) and not re.match(r'^[\d\s]+$', buffer_clean):
                self.log(buffer_clean)
            
            # Check exit
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log("SUCCESS: Flash completed and reboot triggered.")
                self.status = "SUCCESS"
            elif exit_status == 2:
                self.log("SUCCESS: Firmware already up to date (Skipped).")
                self.status = "SKIPPED"
            elif exit_status == -1 and reboot_triggered:
                self.log("SUCCESS: Flash completed and reboot triggered (Connection closed).")
                self.status = "SUCCESS"
            else:
                self.log(f"FAILURE: Process exited with code {exit_status}")
                self.status = "FAILURE"
                
        except Exception as e:
            error_detail = str(e)
            if reboot_triggered:
                 self.log("SUCCESS: Flash completed and reboot triggered (Connection lost).")
                 self.status = "SUCCESS"
            else:
                self.log(f"ERROR: {error_detail}")
                self.status = "FAILURE"
        finally:
            client.close()
            if self.completion_callback:
                # Retrieve error_detail if it was set (only on exception)
                err = locals().get('error_detail', None)
                try:
                     self.completion_callback(self.ip, self.status, err)
                except TypeError:
                     # Fallback for old signature if mismatched
                     self.completion_callback(self.ip, self.status)

def parse_ip_ranges(input_str):
    """
    Parses a string of comma-separated IPs and ranges.
    Supported formats:
    - Single: 192.168.1.10
    - Range: 192.168.1.10-20
    - Range: 192.168.0.100-192.168.0.105 (Not strictly required but good to handle? Sticking to dash for last octet for simplicity as per request)
    Request examples: "192.168.0.1-7, 192.168.0.16-44, 10.8.0.92-203"
    And also supports newlines and spaces.
    """
    ips = set()
    # Split by comma, newline, or space
    parts = [p.strip() for p in re.split(r'[,\s\n]+', input_str) if p.strip()]
    
    for part in parts:
        # Check for range (last octet range like 192.168.1.10-20)
        # Regex to capture: (IP_PREFIX).(START)-(END)
        # e.g. 192.168.1 . 10 - 20
        match = re.match(r'^(\d+\.\d+\.\d+\.)(\d+)-(\d+)$', part)
        if match:
            prefix = match.group(1)
            start = int(match.group(2))
            end = int(match.group(3))
            if start <= end:
                for i in range(start, end + 1):
                    ips.add(f"{prefix}{i}")
            continue
            
        # Check for single IP
        # Basic validation could be improved but sufficient for now
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', part):
            ips.add(part)
            
    return sorted(list(ips), key=lambda ip: socket.inet_aton(ip))
