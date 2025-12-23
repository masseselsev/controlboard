import paramiko
import threading
import time
import socket
import re

class FlashWorker(threading.Thread):
    def __init__(self, ip, username, password, log_queue, completion_callback=None):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.log_queue = log_queue
        self.completion_callback = completion_callback
        self.success = False

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{self.ip}] {message}"
        self.log_queue.put(formatted)

    def run(self):
        self.log("Connecting...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(self.ip, username=self.username, password=self.password, timeout=10)
            self.log("Connected. Starting flash process...")
            
            # Construct the command
            # We use the raw file URL logic similar to setup.sh but ensure it executes non-interactively
            # Note: We need to point to the correct validation/setup script
            # For this task, we assume the standard setup.sh URL which we modified to accept --flash-reboot
            # We use 'dev' branch for testing purposes. Change to 'main' before release if needed.
            cmd = 'url="https://raw.githubusercontent.com/masseselsev/controlboard/dev/dist/setup.sh?v=$(date +%s)"; wget -q -O - "$url" | bash -s "$url" --flash-reboot'
            
            # Execute
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            
            # Stream output
            for line in iter(stdout.readline, ""):
                self.log(line.strip())
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log("SUCCESS: Flash completed and reboot triggered.")
                self.success = True
            else:
                self.log(f"FAILURE: Process exited with code {exit_status}")
                self.success = False
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.success = False
        finally:
            client.close()
            if self.completion_callback:
                self.completion_callback(self.ip, self.success)

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
