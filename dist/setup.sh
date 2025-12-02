#!/bin/bash

# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="14"
# ==================================================

# ================= КОНФИГУРАЦИЯ =================
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="dist"
BRANCH="main"
INSTALL_DIR="$HOME/controlboard"
# ================================================

set -e

# --- ЛОГИРОВАНИЕ ---
GLOBAL_LOG="$HOME/controlboard.log"
STATE_FILE="dev_init.txt" # Локально, потом будет перемещен в $INSTALL_DIR

log_msg() {
    local msg="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SETUP] $msg" >> "$GLOBAL_LOG"
}

track_change() {
    local type="$1"
    local value="$2"
    echo "$type:$value" >> "$STATE_FILE"
    log_msg "Tracked change: $type -> $value"
}

log_msg "--- Запуск setup.sh (v$SCRIPT_VERSION) ---"

sudo_smart() {
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    if echo "admin" | sudo -S -v 2>/dev/null; then
        echo "[sudo] Пароль 'admin' принят автоматически."
        return 0
    fi
    echo "[sudo] Пароль 'admin' не подошел. Введите пароль пользователя:"
    sudo -v
}

# -----------------------------------------------------
# 0. ВЫВОД ВЕРСИИ
# -----------------------------------------------------
if [ -z "$CB_SETUP_RUNNING" ]; then
    echo "--------------------------------------------------"
    echo "   Setup Script Version: $SCRIPT_VERSION"
    echo "--------------------------------------------------"
    export CB_SETUP_RUNNING="true"
fi

# -----------------------------------------------------
# 1. АВТО-КОНФИГУРАЦИЯ
# -----------------------------------------------------
if [ -n "$1" ]; then
    INPUT_URL="$1"
    CLEAN_INPUT_URL="${INPUT_URL%%\?*}"
    if [[ "$CLEAN_INPUT_URL" =~ https://raw.githubusercontent.com/([^/]+)/([^/]+)/([^/]+)/(.+) ]]; then
        GITHUB_USER="${BASH_REMATCH[1]}"
        GITHUB_REPO="${BASH_REMATCH[2]}"
        BRANCH="${BASH_REMATCH[3]}"
        FULL_PATH="${BASH_REMATCH[4]}"
        REPO_FOLDER=$(dirname "$FULL_PATH")
        CURRENT_URL="https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$BRANCH/$REPO_FOLDER/setup.sh"
    fi
else
    CURRENT_URL="https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$BRANCH/$REPO_FOLDER/setup.sh"
fi

download_file() {
    local url=$1
    local dest_dir=$2
    local clean_url="${url%%\?*}"
    local filename=$(basename "$clean_url")
    echo "  -> Скачивание: $filename"
    if curl -s -L -o "$dest_dir/$filename" "$url"; then
        return 0
    else
        echo "[ERROR] Ошибка скачивания $filename"
        return 1
    fi
}

# -----------------------------------------------------
# 2. ПОДГОТОВКА ЗАГРУЗЧИКА
# -----------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
    track_change "DIR" "$INSTALL_DIR"
fi

if [ ! -t 0 ]; then
    echo "==============================================="
    echo "   ПОДГОТОВКА ЗАГРУЗЧИКА..."
    echo "==============================================="
    CACHE_BUST="?t=$(date +%s)"
    SETUP_URL="${CURRENT_URL}${CACHE_BUST}"
    
    if ! curl -s -L -o "$INSTALL_DIR/setup.sh" "$SETUP_URL"; then
        echo "[ОШИБКА] Не удалось скачать скрипт."
        exit 1
    fi
    chmod +x "$INSTALL_DIR/setup.sh"
    exec "$INSTALL_DIR/setup.sh" "$1" < /dev/tty
fi

# =====================================================
#  ДАЛЕЕ ОБЫЧНАЯ РАБОТА
# =====================================================

echo "==============================================="
echo "   УПРАВЛЕНИЕ КОНТРОЛЛЕРОМ"
echo "==============================================="

# -----------------------------------------------------
# 3. ПРОВЕРКА ПРАВ
# -----------------------------------------------------
sudo_smart
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

if ! groups | grep -q "dialout"; then
    echo "[!] Пользователь $USER не имеет доступа к COM-портам."
    echo "    Добавление прав..."
    sudo usermod -aG dialout "$USER"
    track_change "GROUP_USER" "dialout:$USER"
    log_msg "User $USER added to group dialout"
    echo "[OK] Права добавлены. Перезапуск..."
    sleep 1
    exec sg dialout -c "CB_SETUP_RUNNING=true /bin/bash $0 $1"
fi
echo "[OK] Права доступа подтверждены."

# -----------------------------------------------------
# 4. СИНХРОНИЗАЦИЯ ФАЙЛОВ
# -----------------------------------------------------
cd "$INSTALL_DIR"
rm -f *\?t\=*

echo "[*] Синхронизация с GitHub:"
echo "    Источник: $GITHUB_USER/$GITHUB_REPO (Ветка: $BRANCH)"

FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH&t=$(date +%s)" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ОШИБКА] Не удалось получить список файлов."
    exit 1
fi

for url in $FILES_LIST; do
    download_file "$url?t=$(date +%s)" "$INSTALL_DIR"
done

chmod +x autoflash.sh
chmod +x setup.sh

# Перемещаем файл состояния в целевую папку, если он был создан локально
if [ -f "dev_init.txt" ] && [ "$PWD" != "$INSTALL_DIR" ]; then
    mv dev_init.txt "$INSTALL_DIR/"
fi

echo "[OK] Файлы успешно обновлены."
log_msg "Files synchronized."

# -----------------------------------------------------
# 5. СОЗДАНИЕ RUN.SH
# -----------------------------------------------------
RUN_SCRIPT="$INSTALL_DIR/run.sh"
cat > "$RUN_SCRIPT" <<EOF
#!/bin/bash
echo "Запуск обновления и меню..."
url="${CURRENT_URL}?v=\$(date +%s)"
wget -O - "\$url" | bash -s "\$url"
EOF
chmod +x "$RUN_SCRIPT"
echo "[OK] Создан скрипт быстрого запуска: $RUN_SCRIPT"

# -----------------------------------------------------
# 6. ПОДГОТОВКА ОКРУЖЕНИЯ
# -----------------------------------------------------
echo "[*] Проверка системного окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
VENV_PKG="python${PY_VER}-venv"

echo "    Обновление списков пакетов (apt update)..."
sudo apt update > /dev/null 2>&1

echo "    Проверка пакета $VENV_PKG..."
if ! dpkg -s "$VENV_PKG" >/dev/null 2>&1; then
    echo "    Установка $VENV_PKG (может занять время)..."
    if ! sudo apt install -y "$VENV_PKG"; then
        echo "[CRITICAL ERROR] Не удалось установить $VENV_PKG."
        echo "Попробуйте выполнить вручную: sudo apt update && sudo apt install -y $VENV_PKG"
        log_msg "ERROR: Failed to install $VENV_PKG"
        exit 1
    fi
    track_change "PACKAGE" "$VENV_PKG"
    log_msg "Installed package $VENV_PKG"
else
    echo "    Пакет $VENV_PKG уже установлен."
fi

if [ -d "env" ]; then
    if [ ! -f "env/bin/activate" ]; then
        echo "    Обнаружено поврежденное окружение. Пересоздание..."
        rm -rf env
    fi
fi

if [ ! -d "env" ]; then
    echo "    Создание виртуального окружения (env)..."
    if ! python3 -m venv env; then
        echo "[CRITICAL ERROR] Ошибка при создании venv."
        exit 1
    fi
fi

source env/bin/activate
pip install pyserial > /dev/null

echo "[OK] Система готова к работе."

# -----------------------------------------------------
# 7. ИНТЕРАКТИВНОЕ МЕНЮ
# -----------------------------------------------------
while true; do
    echo ""
    echo "=========================================="
    echo "   МЕНЮ УПРАВЛЕНИЯ"
    echo "=========================================="
    echo "1) Консоль управления (app.py)"
    echo "2) Прошивка контроллера (autoflash.sh)"
    echo "3) Выход"
    echo "4) Выход с перезагрузкой системы"
    echo ""
    echo -e "\033[31m00) Полная очистка (dev_cleanup.sh)\033[0m"
    echo ""
    
    read -p "Ваш выбор: " choice

    case $choice in
        1)
            echo "Запуск консоли..."
            python app.py
            ;;
        2)
            echo "Запуск мастера прошивки..."
            ./autoflash.sh
            echo "Нажмите Enter для возврата в меню..."
            read
            ;;
        3)
            echo "Выход."
            exit 0
            ;;
        4)
            echo "Перезагрузка системы..."
            sudo reboot
            ;;
        00)
            echo "Запуск очистки..."
            ./dev_cleanup.sh
            exit 0
            ;;
        *)
            echo "Неверный выбор."
            ;;
    esac
done