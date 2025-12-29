import paramiko
import threading
import time
import socket
import re

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class FlashWorker(threading.Thread):
    def __init__(self, ip, username, password, log_queue, port=22, completion_callback=None, tg_token="", tg_chat_id=""):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.log_queue = log_queue
        self.completion_callback = completion_callback
        self.tg_token = tg_token
        self.tg_chat_id = tg_chat_id
        self.status = "FAILURE" # SUCCESS, SKIPPED, FAILURE
        self.last_log_line = ""

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{self.ip}] {message}"
        self.log_queue.put(formatted)

    def run(self):
        self.log("Connecting...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
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
            
            env_vars = f'export TELEGRAM_BOT_TOKEN="{self.tg_token}"; export TELEGRAM_CHAT_ID="{self.tg_chat_id}"; export TERM=xterm-256color; '
            # Fix CRLF issues by stripping \r with tr or sed
            # wget -q -O - "..." | tr -d '\r' | bash -s "..." --flash-cleanup
            cmd = env_vars + 'mkdir -p ~/controlboard; url="https://raw.githubusercontent.com/masseselsev/controlboard/dev/controlboard/setup.sh?v=$(date +%s)"; if wget -q -O ~/controlboard/setup.sh "$url"; then chmod +x ~/controlboard/setup.sh; ~/controlboard/setup.sh "$url" --flash-cleanup; else echo "Error: Failed to download setup.sh"; exit 1; fi'
            
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
                            clean_content = clean_ansi(line).strip()
                            if clean_content and not any(x in line for x in JUNK_PATTERNS):
                                # Additional filtering for controlboard.py debug output starting with >
                                if clean_content.startswith(">") and "progress" not in clean_content.lower():
                                    pass # Skip debug > lines unless it's progress
                                else:
                                    self.log(line)
                        elif idx_r != -1:
                            line = buffer[:idx_r]
                            # Keep \r for progress bars if valid
                            buffer = buffer[idx_r+1:]
                            clean_content = clean_ansi(line).strip()
                            if ("progress:" in line or "Working" in line or "%" in line) and clean_content:
                                self.log(line + "\r")
                            elif clean_content and not any(x in line for x in JUNK_PATTERNS):
                                if clean_content.startswith(">") and "progress" not in clean_content.lower():
                                    pass
                                else:
                                    self.log(line)
                else:
                    time.sleep(0.01)

            # Flush
            if buffer.strip() and not any(x in buffer for x in JUNK_PATTERNS):
                self.log(buffer)
            
            # Check exit
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log("SUCCESS: Flash completed and reboot triggered.")
                self.status = "SUCCESS"
            elif exit_status == 2:
                self.log("SUCCESS: Firmware already up to date (Skipped).")
                self.status = "SKIPPED"
            else:
                self.log(f"FAILURE: Process exited with code {exit_status}")
                self.status = "FAILURE"
                
        except Exception as e:
            error_detail = str(e)
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
    """
    ips = set()
    parts = [p.strip() for p in input_str.split(',') if p.strip()]
    
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
