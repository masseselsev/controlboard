#!/bin/bash

# ================= ВЕРСИЯ СКРИПТА =================
# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="45"
# ==================================================

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ... (omitted)

    check_fw_version() {
        local retries=3
        local wait_time=5
        
        # Выводим сообщение в stderr чтобы оно отображалось в консоли, но не попадало в переменную возврата
        echo -ne "Поиск контроллера... " >&2

        for ((i=1; i<=retries; i++)); do
            # Ищем ttyUSB* порты (|| true чтобы не вылетал скрипт из-за set -e при отсутствии файлов)
            PORTS=$(ls /dev/ttyUSB* 2>/dev/null || true)
            
            if [ -z "$PORTS" ]; then
                if [ $i -lt $retries ]; then 
                    echo -ne "\rПоиск контроллера... Попытка $i/$retries (не найден, ждем ${wait_time}с)... " >&2
                    sleep $wait_time
                    continue
                fi
                # Возвращаем 0 и пишем статус, чтобы не сработал set -e
                echo -e "\rПоиск контроллера... Не найден.              " >&2
                echo "FAIL"
                return 0
            fi

            for port in $PORTS; do
                echo -ne "\rПоиск контроллера... Попытка $i/$retries (опрос $port)... " >&2
                
                # Используем timeout и команду tech_data
                OUTPUT=$(timeout 3s python dist/controlboard.py read tech_data -p "$port" 2>&1 || true)
                
                # Ищем строку версии обновления. Формат: "  >>> Update Version: 1.1.0"
                if echo "$OUTPUT" | grep -q "Update Version:"; then
                     # Парсим версию
                     RAW_VER=$(echo "$OUTPUT" | grep "Update Version:" | awk -F': ' '{print $2}' | tr -d ' \r')
                     
                     # Форматируем в V01.01.00
                     FULL_VER=$(echo "$RAW_VER" | awk -F. '{printf "V%02d.%02d.%02d", $1, $2, $3}')

                     echo -e "\rПоиск контроллера... [OK] ($FULL_VER)        " >&2
                     echo "OK $FULL_VER"
                     return 0
                fi
            done
            
            if [ $i -lt $retries ]; then 
                echo -ne "\rПоиск контроллера... Попытка $i/$retries (нет ответа, ждем ${wait_time}с)... " >&2
                sleep $wait_time
            fi
        done
        echo -e "\rПоиск контроллера... Нет ответа.              " >&2
        echo "FAIL"
        return 0
    }
    
    FW_VERSION_FILE="$HOME/smalledge_fw_version"
    CURRENT_FW="Неизвестно"
    if [ -f "$FW_VERSION_FILE" ]; then
        CURRENT_FW=$(tail -n 1 "$FW_VERSION_FILE" | awk '{print $NF}')
        # Добавляем V если нет (для совместимости)
        if [[ "$CURRENT_FW" != V* ]] && [[ "$CURRENT_FW" != "Неизвестно" ]]; then
            CURRENT_FW="V$CURRENT_FW"
        fi
    fi
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="controlboard"
BRANCH="dev"
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

echo "--- Настройка платы управления (v$SCRIPT_VERSION) ---"

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
# 1. АВТО-КОНФИГУРАЦИЯ И ПАРСИНГ АРГУМЕНТОВ
# -----------------------------------------------------
AUTO_FLASH_REBOOT=false
AUTO_FLASH_CLEANUP=false

# Проходимся по всем аргументам
for arg in "$@"; do
    if [ "$arg" == "--flash-reboot" ]; then
        AUTO_FLASH_REBOOT=true
    elif [ "$arg" == "--flash-cleanup" ]; then
        AUTO_FLASH_CLEANUP=true
    elif [[ "$arg" =~ https://raw.githubusercontent.com ]]; then
        # Если аргумент похож на URL, используем его
        INPUT_URL="$arg"
    fi
done

if [ -n "$INPUT_URL" ]; then
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



if [ ! -t 0 ] && [ "$AUTO_FLASH_REBOOT" != true ] && [ "$AUTO_FLASH_CLEANUP" != true ]; then
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
    # Передаем все аргументы
    exec "$INSTALL_DIR/setup.sh" "$@" < /dev/tty > /dev/tty
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
    
    # Explicitly resolve script path for restart, handling cases where $0 is bash
    SCRIPT_PATH="$0"
    if [[ "$SCRIPT_PATH" == *"/bash" ]] || [[ "$SCRIPT_PATH" == "bash" ]]; then
       if [ -f "$INSTALL_DIR/setup.sh" ]; then
           SCRIPT_PATH="$INSTALL_DIR/setup.sh"
       elif [ -f "./setup.sh" ]; then
           SCRIPT_PATH="./setup.sh"
       fi
    fi

    # Pass Telegram vars explicitly to survive 'sg' environment reset
    CMD="CB_SETUP_RUNNING=true /bin/bash '$SCRIPT_PATH'"
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        CMD="export TELEGRAM_BOT_TOKEN='$TELEGRAM_BOT_TOKEN'; export TELEGRAM_CHAT_ID='$TELEGRAM_CHAT_ID'; $CMD"
    fi
    exec sg dialout -c "$CMD"
fi
echo -e "[${GREEN}OK${NC}] Права доступа подтверждены."

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

# --- СИНХРОНИЗАЦИЯ ПАПКИ DIST ---
echo "[*] Синхронизация папки dist:"
DIST_DIR="$INSTALL_DIR/dist"
mkdir -p "$DIST_DIR"

FILES_LIST_DIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER/dist?ref=$BRANCH&t=$(date +%s)" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -n "$FILES_LIST_DIST" ]; then
    for url in $FILES_LIST_DIST; do
        download_file "$url?t=$(date +%s)" "$DIST_DIR"
    done
else
    echo "[WARN] Не удалось получить список файлов для dist/."
fi

# Удаляем Windows CRLF переносы строк из скачанных файлов
echo "[INFO] Очистка файлов от CRLF..."
# Try to use sed to strip \r. Using || true to ignore errors if no files match or binary files issue (though unlikely for sh/py)
sed -i 's/\r$//' "$INSTALL_DIR"/*.sh "$INSTALL_DIR"/*.py 2>/dev/null || true

chmod +x autoflash.sh dev_cleanup.sh setup.sh
chmod +x setup.sh
chmod +x dev_cleanup.sh

# Перемещаем файл состояния в целевую папку, если он был создан локально
if [ -f "dev_init.txt" ] && [ "$PWD" != "$INSTALL_DIR" ]; then
    mv dev_init.txt "$INSTALL_DIR/"
fi

echo -e "[${GREEN}OK${NC}] Файлы успешно обновлены."
log_msg "Files synchronized."

# Сохраняем Telegram Credentials (после синхронизации, чтобы не перезаписать)
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "TELEGRAM_BOT_TOKEN=\"$TELEGRAM_BOT_TOKEN\"" > "$INSTALL_DIR/telegram_config.env"
    echo "TELEGRAM_CHAT_ID=\"$TELEGRAM_CHAT_ID\"" >> "$INSTALL_DIR/telegram_config.env"
    log_msg "Telegram config saved from environment."
fi

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
echo -e "[${GREEN}OK${NC}] Создан скрипт быстрого запуска: $RUN_SCRIPT"

# -----------------------------------------------------
# 6. ПОДГОТОВКА ОКРУЖЕНИЯ
# -----------------------------------------------------
echo "[*] Проверка системного окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
VENV_PKG="python${PY_VER}-venv"

echo "    Обновление списков пакетов (apt update)..."
sudo apt update

echo "    Проверка пакета $VENV_PKG..."
if ! dpkg -s "$VENV_PKG" 2>/dev/null | grep -q "Status: install ok installed"; then
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

echo "    Создание виртуального окружения (env)..."
if ! python3 -m venv env; then
    echo "[WARN] Ошибка при создании venv. Возможна проблема с пакетом."
    echo "    Попытка переустановки $VENV_PKG..."
    sudo apt install -y --reinstall "$VENV_PKG"
    
    if ! python3 -m venv env; then
        echo "[CRITICAL ERROR] Не удалось создать venv даже после переустановки."
        exit 1
    fi
fi

source env/bin/activate
pip install pyserial requests

echo -e "[${GREEN}OK${NC}] Система готова к работе."

# -----------------------------------------------------
# 7. АВТОМАТИЧЕСКИЙ РЕЖИМ (ЕСЛИ ЗАДАН ФЛАГ)
# -----------------------------------------------------
if [ "$AUTO_FLASH_REBOOT" = true ] || [ "$AUTO_FLASH_CLEANUP" = true ]; then
    echo "==============================================="
    echo "   РЕЖИМ АВТОМАТИЧЕСКОЙ ПРОШИВКИ"
    if [ "$AUTO_FLASH_CLEANUP" = true ]; then
        echo "   (С ПОСЛЕДУЮЩЕЙ ОЧИСТКОЙ)"
    fi
    echo "==============================================="
    echo -e "[${BLUE}INFO${NC}] Запуск мастера прошивки..."
    
    set +e
    ./autoflash.sh
    EXIT_CODE=$?
    set -e
    
    if [ "$EXIT_CODE" -eq 0 ]; then
        echo -e "[${GREEN}INFO${NC}] Прошивка успешна."
        
        if [ "$AUTO_FLASH_CLEANUP" = true ]; then
            echo "[INFO] Выполнение очистки (dev_cleanup)..."
            cp dev_cleanup.sh /tmp/dev_cleanup_temp.sh
            chmod +x /tmp/dev_cleanup_temp.sh
            /tmp/dev_cleanup_temp.sh
        fi

        echo "[INFO] Перезагрузка..."
        sudo reboot
    elif [ "$EXIT_CODE" -eq 2 ]; then
        echo "[INFO] Прошивка не требуется (версия актуальна)."
        
        if [ "$AUTO_FLASH_CLEANUP" = true ]; then
             echo "[INFO] Выполнение очистки..."
             cp dev_cleanup.sh /tmp/dev_cleanup_temp.sh
             chmod +x /tmp/dev_cleanup_temp.sh
             /tmp/dev_cleanup_temp.sh
        fi
        exit 2
    else
        echo "[ERROR] Ошибка прошивки (код $EXIT_CODE). Выход с ошибкой."
        exit $EXIT_CODE
    fi
    # На всякий случай
    exit 0
fi

# -----------------------------------------------------
# 8. ИНТЕРАКТИВНОЕ МЕНЮ
# -----------------------------------------------------

# Функция проверки версии прошивки перед открытием меню
check_fw_version() {
    local retries=3
    local wait_time=5
    
    # Выводим сообщение в stderr чтобы оно отображалось в консоли, но не попадало в переменную возврата
    echo -ne "Поиск контроллера... " >&2

    for ((i=1; i<=retries; i++)); do
        # Ищем ttyUSB* порты (|| true чтобы не вылетал скрипт из-за set -e при отсутствии файлов)
        PORTS=$(ls /dev/ttyUSB* 2>/dev/null || true)
        
        if [ -z "$PORTS" ]; then
            if [ $i -lt $retries ]; then 
                echo -ne "\rПоиск контроллера... Попытка $i/$retries (не найден, ждем ${wait_time}с)... " >&2
                sleep $wait_time
                continue
            fi
            # Возвращаем 0 и пишем статус, чтобы не сработал set -e
            echo -e "\rПоиск контроллера... Не найден.              " >&2
            echo "FAIL"
            return 0
        fi

        for port in $PORTS; do
            echo -ne "\rПоиск контроллера... Попытка $i/$retries (опрос $port)... " >&2
            
            # Используем timeout и команду tech_data
            OUTPUT=$(timeout 3s python dist/controlboard.py read tech_data -p "$port" 2>&1 || true)
            
            # Ищем строку версии обновления. Формат: "  >>> Update Version: 1.1.0"
            if echo "$OUTPUT" | grep -q "Update Version:"; then
                     # Парсим версию
                     RAW_VER=$(echo "$OUTPUT" | grep "Update Version:" | awk -F': ' '{print $2}' | tr -d ' \r')
                     
                     # Форматируем в V01.01.00
                     FULL_VER=$(echo "$RAW_VER" | awk -F. '{printf "V%02d.%02d.%02d", $1, $2, $3}')

                     echo -e "\rПоиск контроллера... [OK] ($FULL_VER)        " >&2
                     echo "OK $FULL_VER"
                     return 0
            fi
        done
        
        if [ $i -lt $retries ]; then 
            echo -ne "\rПоиск контроллера... Попытка $i/$retries (нет ответа, ждем ${wait_time}с)... " >&2
            sleep $wait_time
        fi
    done
    echo -e "\rПоиск контроллера... Нет ответа.              " >&2
    echo "FAIL"
    return 0
}

while true; do
    FW_VERSION_FILE="$HOME/smalledge_fw_version"
    CURRENT_FW="Неизвестно"
    if [ -f "$FW_VERSION_FILE" ]; then
        CURRENT_FW=$(tail -n 1 "$FW_VERSION_FILE" | awk '{print $NF}')
        # Добавляем V если нет (для совместимости)
        if [[ "$CURRENT_FW" != V* ]] && [[ "$CURRENT_FW" != "Неизвестно" ]]; then
            CURRENT_FW="V$CURRENT_FW"
        fi
    fi
    
    LIVE_STATUS_LINE=$(check_fw_version)
    LIVE_STATUS=$(echo "$LIVE_STATUS_LINE" | awk '{print $1}')
    LIVE_VER=$(echo "$LIVE_STATUS_LINE" | awk '{print $2}')

    if [ "$LIVE_STATUS" == "OK" ]; then
         STATUS_STR="[\033[32mONLINE\033[0m]"
         if [ -n "$LIVE_VER" ]; then
            CURRENT_FW="$LIVE_VER"
            # Update state file so autoflash.sh sees the correct version
            # Strip 'V' prefix for compatibility
            CLEAN_VER="${LIVE_VER#V}"
            # Only append if the last line doesn't already match to avoid spam
            LAST_LOGGED=$(tail -n 1 "$FW_VERSION_FILE" 2>/dev/null | awk '{print $NF}')
            if [ "$LAST_LOGGED" != "$CLEAN_VER" ]; then
                echo "$(date '+%d.%m.%Y, %H:%M') $CLEAN_VER" >> "$FW_VERSION_FILE"
            fi
         fi
    else
         STATUS_STR="[\033[31mOFFLINE\033[0m]"
    fi

    echo ""
    echo "=========================================="
    echo -e "   МЕНЮ УПРАВЛЕНИЯ (VSM2 $CURRENT_FW) $STATUS_STR"
    echo "=========================================="
    echo "1) Консоль управления"
    echo "2) Прошивка контроллера"
    
    # Список доступных прошивок
    if ls dist/Update*.hex 1> /dev/null 2>&1; then
        for f in dist/Update*.hex; do
            echo "   - $(basename "$f")"
        done
    else
        echo "   (нет доступных прошивок)"
    fi

    echo "9) Прошивка и перезагрузка"
    echo "3) Выход с перезагрузкой системы"
    echo "0) Выход"
    echo ""
    echo -e "\033[31m00) Полная очистка (dev_cleanup.sh)\033[0m"
    echo ""
    
    read -p "Ваш выбор: " choice

    case $choice in
        1)
            echo "[INFO] Запуск консоли..."
            python app.py
            ;;
        2)
            echo "[INFO] Запуск мастера прошивки..."
            set +e
            ./autoflash.sh
            set -e
            echo "Нажмите Enter для возврата в меню..."
            read
            ;;
        9)
            echo "[INFO] Запуск мастера прошивки с перезагрузкой..."
            set +e
            ./autoflash.sh
            EXIT_CODE=$?
            set -e
            
            if [ "$EXIT_CODE" -eq 0 ]; then
                echo "[INFO] Прошивка успешна. Перезагрузка через 3 секунды..."
                sleep 3
                sudo reboot
            elif [ "$EXIT_CODE" -eq 2 ]; then
                echo "[INFO] Прошивка не требуется (версия актуальна). Перезагрузка не выполняется."
                echo "Нажмите Enter для возврата в меню..."
                read
            else
                echo "[ERROR] Ошибка прошивки (код $EXIT_CODE). Перезагрузка отменена."
                echo "Нажмите Enter для возврата в меню..."
                read
            fi
            ;;
        3)
            echo "[INFO] Перезагрузка системы..."
            sudo reboot
            ;;
        0)
            echo "[INFO] Выход."
            exit 0
            ;;
        00)
            echo "[INFO] Запуск очистки..."
            ./dev_cleanup.sh
            exit 0
            ;;
        *)
            echo "[WARN] Неверный выбор."
            ;;
    esac
done