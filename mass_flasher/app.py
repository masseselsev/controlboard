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
import git
import threading
import socket  # Added for IP detection
import subprocess # For hostname -I

# --- REPO CACHE SETTINGS ---
# Determine REPO_CACHE_DIR based on environment
if os.path.exists("/app/repo_cache"):
    REPO_CACHE_DIR = "/app/repo_cache"
else:
    REPO_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "repo_cache"))

if not os.path.exists(REPO_CACHE_DIR):
    try:
        os.makedirs(REPO_CACHE_DIR)
    except OSError:
        # Fallback to tmp if current dir is not writable?
        # For now, let it fail or assume current dir is writable
        pass
REPO_URL = "https://github.com/masseselsev/controlboard.git"
REPO_Lock = threading.Lock()

def sync_repo():
    """Background task to sync the repo on startup."""
    with REPO_Lock:
        try:
            # Disable interactive prompts to prevent hanging
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            if not os.path.exists(os.path.join(REPO_CACHE_DIR, '.git')):
                print(f"[REPO] Cloning {REPO_URL} to {REPO_CACHE_DIR}...")
                if not os.path.exists(REPO_CACHE_DIR):
                    os.makedirs(REPO_CACHE_DIR)
                git.Repo.clone_from(REPO_URL, REPO_CACHE_DIR, env=env)
                print("[REPO] Clone complete.")
            else:
                print(f"[REPO] Updating {REPO_CACHE_DIR}...")
                repo = git.Repo(REPO_CACHE_DIR)
                with repo.git.custom_environment(GIT_TERMINAL_PROMPT='0'):
                    # Force fetch and reset to avoid merge conflicts
                    repo.remotes.origin.fetch()
                    repo.git.reset('--hard', 'origin/main')
                    # Also clean untracked files just in case
                    repo.git.clean('-fdx')
                print("[REPO] Update (Fetch+Reset) complete.")
        except Exception as e:
            print(f"[REPO] Sync failed: {e}")

# Start sync in background
threading.Thread(target=sync_repo, daemon=True).start()

TRANSLATIONS = {
    "en": {
        "login_title": "Mass Flasher Login",
        "header_title": "VSM2 Flash&Control",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "new_pass_tg": "New pass via TG Bot",
        "user_created": "User created! You can now login.",
        "enter_user_pass": "Please enter Username and Password to register.",
        "enter_user_first": "Please enter your Username first.",
        "sending_request": "Sending request...",
        "request_failed": "Request failed: ",
        "invalid_credentials": "Invalid credentials",
        "dashboard_title": "VSM2 Flash & Control",
        "logout": "Logout",
        "settings": "Settings",
        "target_devices": "Target Devices",
        "ip_placeholder": "Supported formats: 192.168.1.10, 192.168.1.10-20. Comma separated.",
        "ssh_creds": "SSH Credentials",
        "advanced_settings": "Advanced Settings",
        "advertised_ip_label": "Advertised Flasher IP",
        "advertised_ip_placeholder": "Auto-detect",
        "advertised_ip_desc": "If running in Docker/WSL, set this to your LAN IP so devices can reach back.",
        "start_flash_btn": "Start Mass Flash & Reboot",
        "repo_status_title": "Repository Status",
        "refresh_btn": "Refresh",
        "live_logs_title": "Live Logs",
        "clear_logs_btn": "Clear Logs",
        "close_all_tabs": "Close All Tabs",
        "console_tab": "Console",
        "quick_actions_title": "Quick Actions",
        "config_modal_title": "Configuration",
        "telegram_settings": "Telegram Notification Settings",
        "save_btn": "Save",
        "language_label": "Language / Язык",
        "flash_started": "Flash started",
        "connection_error": "Connection error",
        "please_enter_ips": "Please enter IP addresses",
        "repo_refreshing": "Refreshing...",
        "repo_not_init": "Repo not initialized yet (will sync on startup/first use)",
        "repo_branch": "Branch:",
        "repo_commit": "Commit:",
        "repo_date": "Date:",
        "repo_synced": "Synced:",
        "repo_msg": "Msg:",
        "repo_no_files": "(No files found)",
        "repo_ready_flash": "Ready to Flash",
        "repo_found": "Found:",
        "localhost_warning": "⚠️ ATTENTION!\\n\\nYou are accessing the dashboard via 'localhost'.\\nTarget devices cannot reach 'localhost'.\\n\\nPlease enter your computer's actual LAN IP (e.g., 192.168.1.x) in the 'Advertised Flasher IP' box.",
        "username_label": "Username",
        "password_label": "Password",
        "ssh_port": "SSH Port",
        "advertised_ip_placeholder_required": "REQUIRED: Enter LAN IP (e.g. 192.168.1.50)",
        "loading_text": "Loading...",
        "all_tab": "All",
        "initializing_log_stream": "Initializing log stream...",
        "remote_ip_placeholder": "Remote IP",
        "ssh_port_placeholder": "SSH Port",
        "user_placeholder": "User",
        "pass_placeholder": "Pass",
        "dev_port_placeholder": "Dev Port (Empty=Auto)",
        "dev_port_title": "e.g /dev/ttyUSB0",
        "connect_btn": "Connect",
        "dump_params_title": "Batch Read Parameters",
        "dump_params_btn": "Dump Params",
        "disconnected_status": "DISCONNECTED",
        "read_action": "Read",
        "write_action": "Write",
        "control_action": "Control",
        "util_action": "Util",
        "delete_buttons_title": "Delete Buttons",
        "configure_buttons_title": "Configure Buttons",
        "console_initialized": "Controller Console initialized",
        "console_help_text": "Type 'help' or commands like 'read temp'.",
        "enter_command_placeholder": "Enter command...",
        "customize_quick_actions": "Customize Quick Actions",
        "select_params_to_dump": "Select Parameters to Dump",
        "select_all_btn": "Select All",
        "deselect_all_btn": "Deselect All",
        "execute_dump_btn": "Execute Dump",
        "dump_results_title": "Dump Results",
        "copy_btn": "Copy",
        "download_txt_btn": "Download .txt",
        "close_btn": "Close",
        "settings_title": "Configuration",
        "secrets_saved_desc": "Secrets are saved on the server and never sent to devices.",
        "telegram_settings_title": "Telegram Notification Settings",
        "bot_token_label": "Bot Token",
        "chat_id_label": "Chat ID",
        "language_settings_title": "Language Settings",
        "cancel_btn": "Cancel",
        "close_tab_title": "Close Tab (history preserved in All)",
        "alert_enter_ips": "Please enter IP addresses",
        "alert_localhost_warning": "⚠️ ATTENTION!\\n\\nYou are accessing the dashboard via 'localhost'.\\nTarget devices cannot reach 'localhost'.\\n\\nPlease enter your computer's actual LAN IP (e.g., 192.168.1.x) in the 'Advertised Flasher IP' box.",
        "error_prefix": "Error: ",
        "connection_error_prefix": "Connection error: ",
        "refreshing_text": "Refreshing...",
        "unknown_text": "Unknown",
        "no_files_found": "No files found",
        "ready_to_flash": "Ready to Flash",
        "found_text": "Found",
        "error_saving_settings": "Error saving settings",
        "no_read_commands_found": "No read commands found. Connect and ensure commands are loaded.",
        "alert_select_param": "Select at least one parameter.",
        "reading_please_wait": "Reading... Please wait",
        "connecting_text": "Connecting...",
        "not_connected_no_ip": "Not connected and no IP provided.",
        "connection_failed": "Connection failed",
        "operation_error_prefix": "Operation error: ",
        "scanning_text": "Scanning",
        "no_ports_found": "No ports found",
        "error_scanning": "Error scanning",
        "connected_status": "CONNECTED (Session Active)",
        "disconnect_btn": "Disconnect",
        "disconnected_message": "Disconnected",
        "error_text": "Error",
        "system_text": "System",
        "info_text": "Info",
        "ip_required": "IP Required",
        "connecting_to": "Connecting to",
        "session_lost": "Session Lost",
        "network_error": "Network Error",
        "please_connect_first": "Please connect first",
        "testing_connection": "Testing Connection",
        "reset_usb": "Reset USB",
        "version_short": "Ver",
        "humidity_short": "Hum",
        "ext_temp_short": "Ext Temp",
        "filter_gt_120": "Filter >120",
        "filter_lt_120": "Filter <120",
        "filter_prefix": "Filter",
        "action_cannot_be_deleted": "This action cannot be deleted",
        "click_to_delete": "Click to DELETE"
    },
    "ru": {
        "login_title": "Вход в Mass Flasher",
        "header_title": "VSM2 Прошивка и Управление",
        "username": "Имя пользователя",
        "password": "Пароль",
        "login_btn": "Войти",
        "register_btn": "Регистрация",
        "new_pass_tg": "Сброс пароля через TG",
        "user_created": "Пользователь создан! Теперь вы можете войти.",
        "enter_user_pass": "Введите имя пользователя и пароль для регистрации.",
        "enter_user_first": "Сначала введите имя пользователя.",
        "sending_request": "Отправка запроса...",
        "request_failed": "Ошибка запроса: ",
        "invalid_credentials": "Неверные учетные данные",
        "dashboard_title": "VSM2 Прошивка и Управление",
        "logout": "Выйти",
        "settings": "Настройки",
        "target_devices": "Целевые Устройства",
        "ip_placeholder": "Поддерживаемые форматы: 192.168.1.10, 192.168.1.10-20. Через запятую.",
        "ssh_creds": "Учетные данные SSH",
        "advanced_settings": "Расширенные настройки",
        "advertised_ip_label": "Публичный IP Флешера",
        "advertised_ip_placeholder": "Авто-определение",
        "advertised_ip_desc": "Если запуск в Docker/WSL, укажите IP вашего ПК в локальной сети.",
        "start_flash_btn": "Начать Прошивку и Перезагрузить",
        "repo_status_title": "Статус Репозитория",
        "refresh_btn": "Обновить",
        "live_logs_title": "Логи в реальном времени",
        "clear_logs_btn": "Очистить",
        "close_all_tabs": "Закрыть все вкладки",
        "console_tab": "Консоль",
        "quick_actions_title": "Быстрые Действия",
        "config_modal_title": "Настройки",
        "telegram_settings": "Настройки уведомлений Telegram",
        "save_btn": "Сохранить",
        "language_label": "Language / Язык",
        "flash_started": "Процесс запущен",
        "connection_error": "Ошибка подключения",
        "please_enter_ips": "Пожалуйста, введите IP адреса",
        "repo_refreshing": "Обновление...",
        "repo_not_init": "Репозиторий не инициализирован (синхронизация при первом запуске)",
        "repo_branch": "Ветка:",
        "repo_commit": "Коммит:",
        "repo_date": "Дата:",
        "repo_synced": "Синхр.:",
        "repo_msg": "Сообщ.:",
        "repo_no_files": "(Файлы не найдены)",
        "repo_ready_flash": "Готов к прошивке",
        "repo_found": "Найдено:",
        "localhost_warning": "⚠️ ВНИМАНИЕ!\\n\\nВы зашли через 'localhost'.\\nУстройства не смогут подключиться к 'localhost'.\\n\\nПожалуйста, введите реальный IP вашего компьютера (например, 192.168.1.x) в поле 'Публичный IP Флешера'.",
        "username_label": "Имя пользователя",
        "password_label": "Пароль",
        "ssh_port": "SSH Порт",
        "advertised_ip_placeholder_required": "ОБЯЗАТЕЛЬНО: Введите IP LAN (напр. 192.168.1.50)",
        "loading_text": "Загрузка...",
        "all_tab": "Все",
        "initializing_log_stream": "Инициализация потока логов...",
        "remote_ip_placeholder": "Удаленный IP",
        "ssh_port_placeholder": "SSH Порт",
        "user_placeholder": "Польз.",
        "pass_placeholder": "Пароль",
        "dev_port_placeholder": "Порт Устр. (Пусто=Авто)",
        "dev_port_title": "напр. /dev/ttyUSB0",
        "connect_btn": "Подкл.",
        "dump_params_title": "Пакетное чтение параметров",
        "dump_params_btn": "Чтение Парам.",
        "disconnected_status": "ОТКЛЮЧЕНО",
        "read_action": "Чтение",
        "write_action": "Запись",
        "control_action": "Контроль",
        "util_action": "Утилиты",
        "delete_buttons_title": "Удалить кнопки",
        "configure_buttons_title": "Настроить кнопки",
        "console_initialized": "Консоль Контроллера инициализирована",
        "console_help_text": "Введите 'help' или команды, например 'read temp'.",
        "enter_command_placeholder": "Введите команду...",
        "customize_quick_actions": "Настройка Быстрых Действий",
        "select_params_to_dump": "Выберите параметры для выгрузки",
        "select_all_btn": "Выбрать Все",
        "deselect_all_btn": "Снять Выбор",
        "execute_dump_btn": "Выполнить Выгрузку",
        "dump_results_title": "Результаты Выгрузки",
        "copy_btn": "Копировать",
        "download_txt_btn": "Скачать .txt",
        "close_btn": "Закрыть",
        "settings_title": "Конфигурация",
        "secrets_saved_desc": "Секретные данные хранятся на сервере и не отправляются на устройства.",
        "telegram_settings_title": "Настройки уведомлений Telegram",
        "bot_token_label": "Токен Бота",
        "chat_id_label": "ID Чата",
        "language_settings_title": "Настройки Языка",
        "cancel_btn": "Отмена",
        "close_tab_title": "Закрыть вкладку (история сохранится во 'Все')",
        "alert_enter_ips": "Пожалуйста, введите IP адреса",
        "alert_localhost_warning": "⚠️ ВНИМАНИЕ!\\n\\nВы зашли через 'localhost'.\\nУстройства не смогут подключиться к 'localhost'.\\n\\nПожалуйста, введите реальный IP вашего компьютера (например, 192.168.1.x) в поле 'Публичный IP Флешера'.",
        "error_prefix": "Ошибка: ",
        "connection_error_prefix": "Ошибка подключения: ",
        "refreshing_text": "Обновление...",
        "unknown_text": "Неизвестно",
        "no_files_found": "Файлы не найдены",
        "ready_to_flash": "Готов к прошивке",
        "found_text": "Найдено",
        "error_saving_settings": "Ошибка сохранения настроек",
        "no_read_commands_found": "Команды чтения не найдены. Подключитесь.",
        "alert_select_param": "Выберите хотя бы один параметр.",
        "reading_please_wait": "Чтение... Подождите",
        "connecting_text": "Подключение...",
        "not_connected_no_ip": "Нет подключения и не указан IP.",
        "connection_failed": "Ошибка подключения",
        "operation_error_prefix": "Ошибка операции: ",
        "scanning_text": "Сканирование",
        "no_ports_found": "Порты не найдены",
        "error_scanning": "Ошибка сканирования",
        "connected_status": "ПОДКЛЮЧЕНО (Сессия активна)",
        "disconnect_btn": "Отключить",
        "disconnected_message": "Отключено",
        "error_text": "Ошибка",
        "system_text": "Система",
        "info_text": "Инфо",
        "ip_required": "Требуется IP",
        "connecting_to": "Подключение к",
        "session_lost": "Сессия потеряна",
        "network_error": "Ошибка сети",
        "please_connect_first": "Сначала подключитесь",
        "testing_connection": "Тест подключения",
        "reset_usb": "Сброс USB",
        "version_short": "Вер",
        "humidity_short": "Влаж",
        "ext_temp_short": "Внеш Темп",
        "filter_gt_120": "Фильтр >120",
        "filter_lt_120": "Фильтр <120",
        "filter_prefix": "Filter",  # Keep filter prefix logic in English or map it? Command is consistent, label changes.
        "action_cannot_be_deleted": "Это действие нельзя удалить",
        "click_to_delete": "Нажмите, чтобы УДАЛИТЬ"
    }
}

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_for_prod' 
log_queue = queue.Queue() # Ingestion queue (Producers write here)

# Broadcast System
subscribers = []
LOG_HISTORY = []
MAX_HISTORY = 500

def broadcast_logger():
    """Reads from log_queue and broadcasts to all subscribers."""
    while True:
        try:
            msg = log_queue.get()
            
            # Save to history
            LOG_HISTORY.append(msg)
            if len(LOG_HISTORY) > MAX_HISTORY:
                LOG_HISTORY.pop(0)
            
            # Broadcast
            # Iterate copy of subscribers in case of modification during iteration
            for sub in subscribers[:]:
                try:
                    sub.put(msg)
                except:
                    pass
        except Exception as e:
            print(f"Broadcast Error: {e}")
            gevent.sleep(0.1)


import gevent
import time


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
    
    message = f"<b>[VSM2 Flash&Control]</b>\n{status_icon} <b>Отчет о прошивке</b>\n\n" \
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

# --- RESET PASSWORD LOGIC ---

def password_reset_worker(username, token, chat_id):
    """
    Polls Telegram for responses for 60 seconds.
    If a message is received from chat_id, it is set as the new password.
    """
    print(f"[RESET] Starting reset watcher for {username}")
    
    # 1. Get current update_id offset to ignore old messages
    offset = None
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        res = requests.get(url, params={"limit": 1}, timeout=5)
        if res.ok:
            updates = res.json().get('result', [])
            if updates:
                offset = updates[-1]['update_id'] + 1
    except Exception as e:
        print(f"[RESET] Error getting initial offset: {e}")

    start_time = time.time()
    
    while time.time() - start_time < 60:
        try:
            # Poll for updates
            payload = {"timeout": 10, "allowed_updates": ["message"]}
            if offset:
                payload['offset'] = offset
                
            res = requests.post(f"https://api.telegram.org/bot{token}/getUpdates", json=payload, timeout=12)
            
            if not res.ok:
                time.sleep(1)
                continue
                
            updates = res.json().get('result', [])
            
            for u in updates:
                offset = u['update_id'] + 1
                msg = u.get('message', {})
                sender_id = str(msg.get('chat', {}).get('id', ''))
                
                # Verify sender matches config
                if sender_id == str(chat_id):
                    text = msg.get('text', '').strip()
                    if text:
                        print(f"[RESET] Received new password for {username}")
                        
                        # Set new password
                        users = load_users()
                        users[username] = generate_password_hash(text)
                        save_users(users)
                        
                        # Notify User via Telegram
                        reply_url = f"https://api.telegram.org/bot{token}/sendMessage"
                        requests.post(reply_url, json={
                            "chat_id": chat_id,
                            "text": f"<b>[VSM2 Flash&Control]</b>\n✅ Password successfully updated for user '{username}'.\nYou can now login.",
                            "parse_mode": "HTML"
                        })
                        return # Done
                        
            gevent.sleep(1) # Yield
            
        except Exception as e:
            print(f"[RESET] Polling error: {e}")
            gevent.sleep(2)

    # Timeout
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
            "chat_id": chat_id,
            "text": "<b>[VSM2 Flash&Control]</b>\n⏳ Password reset request timed out.",
            "parse_mode": "HTML"
        })
    except:
        pass


@app.route('/api/reset/request', methods=['POST'])
def request_password_reset():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "Username required"}), 400
        
    users = load_users()
    if username not in users:
        # Security: Don't reveal user existence? Or local tool is fine?
        # For this tool, better to give feedback.
        return jsonify({"error": "User not found"}), 404
        
    config = load_user_config(username)
    token = config.get('telegram_token')
    chat_id = config.get('telegram_chat_id')
    
    if not token or not chat_id:
        return jsonify({"error": "Telegram Bot not configured for this user. Cannot reset."}), 400
        
    # Send Prompt
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        msg = f"<b>[VSM2 Flash&Control]</b>\n🔐 <b>Password Reset Request</b>\n\nUser '{username}' requested a password reset.\n\nReply to this message with your new password within <b>60 seconds</b>."
        
        res = requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
        
        if not res.ok:
            return jsonify({"error": f"Failed to contact Telegram API: {res.text}"}), 500
            
        # Spawn Worker
        gevent.spawn(password_reset_worker, username, token, chat_id)
        
        return jsonify({"message": "Request sent! Check your Telegram and reply with the new password within 1 minute."})
        
    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"}), 500


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
            lang = session.get('pre_login_lang', 'en')
            t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
            return render_template('login.html', error=t["invalid_credentials"], t=t, current_lang=lang)
            
    lang = request.args.get('lang')
    if lang:
        session['pre_login_lang'] = lang
    else:
        lang = session.get('pre_login_lang', 'en')
        
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    return render_template('login.html', t=t, current_lang=lang)

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

# --- CONFIG & VERSION ---
APP_VERSION = "1.2.1"

def get_available_ips():
    """Returns a list of all IPv4 addresses on the host."""
    ips = []
    try:
        # Method 1: hostname -I (Debian/Ubuntu)
        result = subprocess.check_output(['hostname', '-I'], timeout=2).decode().strip()
        ips.extend(result.split())
    except:
        pass
        
    try:
        # Method 2: socket (Fallback main IP)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
            if ip not in ips:
                ips.append(ip)
        except Exception:
            pass
        finally:
            s.close()
    except:
        pass
        
    # Remove duplicates and loopback
    unique_ips = []
    for ip in ips:
        if ip and not ip.startswith('127.') and ip not in unique_ips:
            unique_ips.append(ip)
    return unique_ips

@app.route('/')
@login_required
def index():
    config = load_user_config(session['user'])
    lang = config.get('language', 'en')
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    available_languages = {"en": "English", "ru": "Русский"}
    
    local_ips = get_available_ips()
    
    return render_template('index.html', 
                          user=session['user'], 
                          version=APP_VERSION, 
                          t=t, 
                          current_lang=lang, 
                          available_languages=available_languages,
                          local_ips=local_ips)

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
                
            if request.form.get('language') is not None:
                config['language'] = request.form.get('language')
            
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
    
    # --- AUTO-UPDATE REPO ---
    # Trigger a git pull to ensure we are flashing the absolute latest version.
    log_queue.put("[SYSTEM] Checking for repository updates...")
    # Run sync in main thread (blocking) or background? 
    # Blocking is safer to ensure we don't flash old code while pulling.
    try:
         sync_repo()
         log_queue.put("[SYSTEM] Repository check complete.")
    except Exception as e:
         log_queue.put(f"[SYSTEM] [WARN] Repository update failed: {e}")
    
    config = load_user_config(username)
    tg_token = config.get("telegram_token", "")
    tg_chat_id = config.get("telegram_chat_id", "")

    # Create a closure to capture token/chat_id for THIS batch
    def notification_callback(ip, status, error_detail=None):
        send_telegram_notification(ip, status, tg_token, tg_chat_id, error_detail)

    # Detect Host IP to advertise to devices (solves Docker networking issues)
    # Priority:
    # 1. User-supplied IP from UI
    # 2. Host header IP (if valid external IP)
    # 3. Fallback to auto-detection
    
    advertised_ip = data.get('advertised_ip', '').strip()
    
    if not advertised_ip:
        # If using Docker, 'request.host' usually contains the external access IP (Host header)
        advertised_ip = request.host.split(':')[0]
    
    log_queue.put(f"[SYSTEM] Advertising Host IP: {advertised_ip} (Version: {APP_VERSION})")

    for ip in ips:
        # Pass callback
        worker = FlashWorker(ip, ssh_user, ssh_pass, log_queue, port=port, 
                           completion_callback=notification_callback, 
                           tg_token=tg_token, tg_chat_id=tg_chat_id,
                           advertised_ip=advertised_ip)
        worker.start()
        
    return jsonify({"status": "started", "count": len(ips)})


@app.route('/api/repo/status')
@login_required
def get_repo_status():
    """Returns the current git status of the cached repo."""
    status = {
        "exists": False,
        "commit": None,
        "author": None,
        "date": None,
        "message": None,
        "branch": "unknown",
        "last_synced": None
    }
    
    if os.path.exists(os.path.join(REPO_CACHE_DIR, '.git')):
        status["exists"] = True
        try:
            repo = git.Repo(REPO_CACHE_DIR)
            head = repo.head.commit
            status["commit"] = head.hexsha[:7]
            status["author"] = str(head.author)
            status["date"] = str(head.committed_datetime)
            status["message"] = head.message.strip()
            status["branch"] = repo.active_branch.name
            
            # Get timestamp of the FETCH_HEAD to see when we last talked to remote, 
            # OR just use file mtime of a key file
            fetch_head = os.path.join(REPO_CACHE_DIR, '.git', 'FETCH_HEAD')
            if os.path.exists(fetch_head):
                import datetime
                mtime = os.path.getmtime(fetch_head)
                status["last_synced"] = str(datetime.datetime.fromtimestamp(mtime))
            else:
                 status["last_synced"] = "Never (Local only?)"
        except Exception as e:
            status["error"] = str(e)
            
    return jsonify(status)

@app.route('/stream')
@login_required
def stream():
    def event_stream():
        # User-specific queue
        q = queue.Queue()
        subscribers.append(q)
        
        try:
            # 1. Send History (Catch up)
            for old_msg in list(LOG_HISTORY):
                yield f"data: {old_msg}\n\n"
            
            # 2. Stream new messages
            while True:
                try:
                    # Heartbeat every 10s
                    message = q.get(timeout=10)
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        finally:
            # Clean up
            if q in subscribers:
                subscribers.remove(q)
    
    return Response(event_stream(), mimetype="text/event-stream")

import subprocess
import glob
import sys

# Add dist to sys.path to import commands definition for autocomplete
sys.path.append(os.path.join(os.path.dirname(__file__), 'dist'))
# Also add local development path (now mounted at /app/controlboard_repo/dist)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'controlboard_repo', 'dist')))
# Fallback for local non-docker dev
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

@app.route('/api/logs/clear', methods=['POST'])
@login_required
def clear_server_logs():
    global LOG_HISTORY
    LOG_HISTORY.clear()
    return jsonify({"status": "cleared"})


# --- FILE SERVER FOR OFFLINE FLASHING ---

from flask import send_from_directory

@app.route('/files/<path:filename>')
def serve_repo_file(filename):
    """Serves files from the local repo cache."""
    return send_from_directory(REPO_CACHE_DIR, filename)

@app.route('/api/repo/list')
def list_repo_files():
    """
    Mimics GitHub API to list files in a directory.
    Query param: path (relative to repo root)
    Returns: JSON list of objects with 'download_url' and 'type'
    """
    rel_path = request.args.get('path', '')
    # Secure path to prevent traversal
    safe_path = os.path.normpath(os.path.join(REPO_CACHE_DIR, rel_path))
    if not safe_path.startswith(REPO_CACHE_DIR):
        return jsonify([]), 403
        
    if not os.path.exists(safe_path) or not os.path.isdir(safe_path):
        return jsonify([]), 404
        
    files = []
    # host_url includes scheme and host (http://IP:5000)
    base_url = request.host_url.rstrip('/') 
    
    for item in os.listdir(safe_path):
        item_path = os.path.join(safe_path, item)
        item_rel = os.path.join(rel_path, item)
        
        if os.path.isfile(item_path):
            files.append({
                "name": item,
                "type": "file",
                # GitHub logic: download_url
                "download_url": f"{base_url}/files/{item_rel}"
            })
        elif os.path.isdir(item_path):
             files.append({
                "name": item,
                "type": "dir",
                 "download_url": None
             })
             
    return jsonify(files)
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

    # Determine Local IP (Base URL)
    # We need the IP of the interface that connects to the target.
    # We can get this *after* connecting via SSH (client.get_transport().sock.getsockname()[0])
    # BUT we need to pass it to FlashWorker/setup.sh later? 
    # Actually, for CONSOLE connect we don't need it yet, but for FLASH we do.
    # However, console connect ALSO does bootstrap! 
    # The bootstrap in console_connect uses SFTP, so it doesn't need HTTP.
    # Only FlashWorker uses setup.sh which needs HTTP.
    
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
            # Auto-Deploy from local sources
            # We assume the controlboard repo is mounted at /app/controlboard_repo
            repo_path = "/app/controlboard_repo"
            dist_path = os.path.join(repo_path, "dist")
            
            if not os.path.exists(repo_path):
                # Fallback if running outside docker or path diff (local dev)
                repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "controlboard"))
                dist_path = os.path.join(repo_path, "dist") 
            
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
                # 1. app.py (from repo root)
                local_app_py = os.path.join(repo_path, "app.py")
                if os.path.exists(local_app_py):
                    sftp.put(local_app_py, "controlboard/app.py")
                else:
                    log_boot(f"[WARN] Local app.py not found at {local_app_py}")

                # 2. dist files (commands.py, controlboard.py)
                for fname in ['commands.py', 'controlboard.py']:
                    local_path = os.path.join(dist_path, fname)
                    remote_path = f"controlboard/dist/{fname}" # keep inside dist/ on remote?
                    # correction: setup.sh structure has 'dist' folder? 
                    # Checking setup.sh: it downloads to $INSTALL_DIR/dist. 
                    # But wait, remote structure usually has app.py in root and dist/ folder?
                    # Original code put them in "controlboard/{fname}" which implies flat structure?
                    # Let's check imports in app.py. It does `sys.path.append... dist`.
                    # checking setup.sh again:
                    # Line 267: DIST_DIR="$INSTALL_DIR/dist"
                    # So dist files go to dist/. 
                    # BUT app.py in repo is in root.
                    # The previous code: `remote_path = f"controlboard/{fname}"` for all files.
                    # That seems wrong if imports expect dist.
                    # However, let's stick to flat if that's what was intended, OR fix it.
                    # checking remote app.py usage... 
                    # Remote app.py: tries to import commands. 
                    # If commands.py is in same dir, it works. 
                    # If it's in dist, we need sys.path.append.
                    # Let's check local app.py lines 407+: it appends 'dist'.
                    # So remote structure should PROBABLY reflect local structure.
                    #   ~/controlboard/app.py
                    #   ~/controlboard/dist/commands.py
                    #   ~/controlboard/dist/controlboard.py
                    
                    ssh.exec_command("mkdir -p ~/controlboard/dist")
                    
                    remote_dist_path = f"controlboard/dist/{fname}"
                    if os.path.exists(local_path):
                        sftp.put(local_path, remote_dist_path)
                    else:
                        log_boot(f"[WARN] Local {fname} not found at {local_path}")
                
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
        
        # Filter out shell startup noise (Last login, sg dialout echo, etc.)
        # We look for the start of the actual app output.
        banner_marker = "--- Интерактивный терминал контроллера ---"
        if banner_marker in clean_output:
            idx = clean_output.find(banner_marker)
            # Remove everything before banner
            clean_output = clean_output[idx:]
            # Ensure it starts clean
            # Clean interaction prompts
            # Remove "Введите COM-порт..." and "Введите baudrate..." lines including inputs
            # The input might be on the same line or next line depending on echo. 
            # We just matched widely.
            clean_output = re.sub(r"Введите COM-порт.*?\n", "", clean_output)
            clean_output = re.sub(r"Введите baudrate.*?\n", "", clean_output)
            # Cleanup multiple newlines
            clean_output = re.sub(r"\n{3,}", "\n\n", clean_output)
            
            clean_output = clean_output.lstrip()
        elif "Interactive terminal" in clean_output: # Fallback English
             idx = clean_output.find("Interactive terminal")
             clean_output = clean_output[idx:]
            
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
        if isinstance(channel, str):
             # Still mostly likely bootstapping, return temporary message
             return jsonify({"output": "[System] Busy initializing... please wait."})

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






@app.route('/api/console/batch_read', methods=['POST'])
@login_required
def console_batch_read():
    username = session['user']
    if username not in CONSOLE_SESSIONS:
        return jsonify({"error": "Not connected"}), 400
        
    channel = CONSOLE_SESSIONS[username]
    if isinstance(channel, str):
        return jsonify({"error": "Console busy initializing"}), 400

    data = request.json
    commands_list = data.get('commands', [])
    
    if not commands_list:
        return jsonify({"error": "No commands provided"}), 400
        
    import re
    import time
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    full_output = []
    full_output.append(f"--- Batch Dump ({len(commands_list)} items) ---")
    full_output.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    full_output.append("-" * 40)
    
    try:
        for cmd in commands_list:
            full_output.append(f"> read {cmd}")
            # Ensure we send a clean command
            channel.send(f"read {cmd}\n") 
            
            # Wait for processing
            time.sleep(0.2) 
            
            output = ""
            attempts = 0
            # Wait loop
            while attempts < 10:
                if channel.recv_ready():
                    chunk = channel.recv(4096).decode('utf-8', errors='ignore')
                    output += chunk
                    # Heuristic: if we see the prompt '$', we might be done.
                    # But prompt might be at the end. 
                    # simple wait for now.
                    attempts = 0 # reset if we get data
                else:
                    time.sleep(0.1)
                    attempts += 1
            
            clean = ansi_escape.sub('', output).strip()
            # Try to filter out the echo
            # e.g. "read temp\n25.0\n$"
            lines = clean.split('\n')
            filtered_lines = [l for l in lines if f"read {cmd}" not in l and "$" not in l]
            result_text = "\n".join(filtered_lines).strip()
            
            if not result_text:
                result_text = clean # Fallback if filtering removed everything
                
            full_output.append(result_text)
            full_output.append("-" * 20)
            
        return jsonify({"text": "\n".join(full_output)})

    except Exception as e:
        # Don't delete session blindly on batch error, it might be recoverable
        print(f"Batch Error: {e}")
        return jsonify({"error": f"Batch Error: {str(e)}"}), 500


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
    # Start the log broadcaster
    gevent.spawn(broadcast_logger)
    
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    print("Serving on http://0.0.0.0:5000")
    http_server.serve_forever()
