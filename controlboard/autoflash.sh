#!/bin/bash

# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="27"
# ==================================================

#----------------------------------------------------------------------
# Скрипт для автоматической прошивки контроллера.
# Функции: Поиск порта, остановка служб, заморозка WDT, прошивка, лог.
#----------------------------------------------------------------------

# Выход при любой ошибке
set -e

echo "--- Автоматический прошивальщик контроллера (v$SCRIPT_VERSION) ---"

# --- ЛОГИРОВАНИЕ ---
GLOBAL_LOG="$HOME/controlboard.log"
STATE_FILE="dev_init.txt"

log_msg() {
    local msg="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $msg" >> "$GLOBAL_LOG"
}

track_change() {
    local type="$1"
    local value="$2"
    echo "$type:$value" >> "$STATE_FILE"
    log_msg "Tracked change: $type -> $value"
}

log_msg "--- Запуск autoflash.sh (v$SCRIPT_VERSION) ---"

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

# --- ШАГ 1: ПОИСК ФАЙЛОВ ---
echo -e "\n[1/7] Поиск необходимых файлов..."

if [ ! -f "dist/controlboard.py" ] || [ ! -f "dist/commands.py" ]; then
    echo "ОШИБКА: Не найдены файлы 'controlboard.py' или 'commands.py' в 'dist/'."
    exit 1
fi
echo "  [OK] Скрипты обнаружены."


# --- ОТОБРАЖЕНИЕ ТЕКУЩЕЙ ВЕРСИИ ---
FW_VERSION_FILE="$HOME/smalledge_fw_version"
if [ -f "$FW_VERSION_FILE" ]; then
    CURRENT_FW=$(tail -n 1 "$FW_VERSION_FILE" | awk '{print $NF}')
    echo "  [INFO] Текущая версия прошивки: $CURRENT_FW"
else
    echo "  [INFO] Файл с версией отсутствует, предположительно заводская прошивка."
fi

HEX_FILES=()
# Ищем файлы и сортируем их по алфавиту
while IFS= read -r -d '' file; do
    HEX_FILES+=("$(basename "$file")")
done < <(find dist/ -maxdepth 1 -name "Update*.hex" -print0 | sort -z)

FILE_COUNT=${#HEX_FILES[@]}
HEX_FILE=""

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "[ERROR] .hex файл прошивки не найден."
    exit 1
elif [ "$FILE_COUNT" -eq 1 ]; then
    HEX_FILE=${HEX_FILES[0]}
    echo "  [OK] Найден один файл прошивки: $HEX_FILE"
else
    echo "  - Найдено несколько файлов прошивки. Выберите нужный:"
    for i in "${!HEX_FILES[@]}"; do
        echo "    $((i+1))) ${HEX_FILES[$i]}"
    done
    
    echo ""
    echo "    0) Отмена, выход в предыдущее меню"
    
    echo ""
    read -p "Введите номер файла (0-$FILE_COUNT): " CHOICE
    
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
        echo "[ERROR] Неверный ввод."
        exit 1
    fi

    if [ "$CHOICE" -eq 0 ]; then
        echo "[INFO] Отмена операции."
        exit 0
    fi

    if [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "$FILE_COUNT" ]; then
        echo "[ERROR] Неверный номер."
        exit 1
    fi
    HEX_FILE=${HEX_FILES[$((CHOICE-1))]}
    echo "  [OK] Выбрана прошивка: $HEX_FILE"
    HEX_FILE=${HEX_FILES[$((CHOICE-1))]}
    echo "  [OK] Выбрана прошивка: $HEX_FILE"
fi

# --- ПРОВЕРКА ВЕРСИИ ---
FIRM_VERSION="00.00.00"
if [[ $HEX_FILE =~ V([0-9]{2}\.[0-9]{2}\.[0-9]{2}) ]]; then
    FIRM_VERSION=${BASH_REMATCH[1]}
else
    echo "[WARN] Не удалось определить версию из имени файла. Принудительная прошивка разрешена."
fi

# --- 1.5 ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ТЕКУЩЕЙ ВЕРСИИ И ТИПЕ ---
echo "  -> Проверка текущей версии на устройстве..."
# Scan again to get full details (port is already found but we need context if not passed, 
# actually step 4 finds the port. Wait, step 4 is BELOW.
# We need to move port detection UP or utilize step 4's result? 
# The script structure is linear. Step 4 finds the port. 
# Logic fix: We can't check version at step 1 fully if we haven't found the port.
# BUT, the script structure checks FILE version (dist/) vs CACHED version (smalledge_fw_version).
# We need to change this to CHECK DEVICE version.
# However, autoflash usually assumes we optimize by checking file first.
# User wants: "For example: ' >>> Active Firmware: Factory'. If Factory, then firmware must be executed."
# This implies we MUST query the device. 
# So we need to move Port Detection (Step 4) BEFORE Version Check (currently Step 1 part 2).

# REORDERING:
# 1. Search Files
# 2. Setup Env
# 3. Stop Services
# 4. Find Port (AND GET DATA)
# 5. Decision (Update or Skip)
# 6. Freezer/Update
# ...

# We will modify the flow slightly. We will keep Step 1 (File Search) but defer the "Skip" decision.

# ... (Moving on to actual code modification)

# Removing early check in Step 1.
# (We will delete Lines 121-146 in Step 1 and move logic after Step 4)


echo "  -> Будет установлена версия: $FIRM_VERSION"

# --- ШАГ 2: НАСТРОЙКА ОКРУЖЕНИЯ ---
echo -e "\n[2/7] Настройка Python окружения..."

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ОШИБКА: Требуется Python версии 3.10 или выше."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
sudo_smart

# Проверяем, установлен ли пакет, перед установкой
VENV_PKG="python${PY_VER}-venv"
if ! dpkg -s "$VENV_PKG" >/dev/null 2>&1; then
    sudo apt install -y "$VENV_PKG" > /dev/null 2>&1 || true
    track_change "PACKAGE" "$VENV_PKG"
    log_msg "Installed package $VENV_PKG"
else
    # Уже установлен, просто убеждаемся (без трекинга)
    sudo apt install -y "$VENV_PKG" > /dev/null 2>&1 || true
fi

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
echo "  - Установка зависимостей (pyserial)..."
pip install pyserial requests > /dev/null

# --- ШАГ 3: ОСТАНОВКА СЛУЖБ ---
echo -e "\n[3/7] Временная остановка служб для доступа к порту..."
sudo service edgeserver stop
sudo service vsmd stop
echo "Службы остановлены. Порт свободен."

# --- ШАГ 4: ПОИСК ПОРТА ---
echo -e "\n[4/7] Поиск контроллера на COM-портах..."
FOUND_PORT=""
set +e
ACTIVE_FW_TYPE="Unknown"
DETECTED_VER=""

for port in /dev/ttyUSB{0,1,2,3,4}; do
    [ -e "$port" ] || continue
    echo -n "  - Проверка $port... "
    # Request tech_data to get full info
    OUTPUT=$(python dist/controlboard.py read tech_data -p "$port" 2>&1)
    
    if echo "$OUTPUT" | grep -q "Active Firmware:"; then
        FOUND_PORT="$port"
        
        # Parse Type
        if echo "$OUTPUT" | grep -q "Active Firmware: Factory"; then
            ACTIVE_FW_TYPE="Factory"
        elif echo "$OUTPUT" | grep -q "Active Firmware: Update"; then
             ACTIVE_FW_TYPE="Update"
        fi
        
        # Parse Version (Update Version)
        # Format: "  >>> Update Version: 1.1.0"
        RAW_VER=$(echo "$OUTPUT" | grep "Update Version:" | awk -F': ' '{print $2}' | tr -d ' \r')
        if [ -n "$RAW_VER" ]; then
             DETECTED_VER=$(echo "$RAW_VER" | awk -F. '{printf "V%02d.%02d.%02d", $1, $2, $3}')
        fi

        echo "OK! ($ACTIVE_FW_TYPE, $DETECTED_VER)"
        break
    else
        echo "Нет ответа."
    fi
done
set -e

if [ -z "$FOUND_PORT" ]; then
    echo "ОШИБКА: Не удалось найти контроллер."
    echo "[!] АВАРИЙНЫЙ ЗАПУСК СЛУЖБ..."
    sudo service edgeserver start
    sudo service vsmd start
    deactivate
    exit 1
fi

# --- 4.5 РЕШЕНИЕ ОБ ОБНОВЛЕНИИ ---
echo -e "\n[4.5/7] Проверка необходимости обновления..."
echo "  Активная прошивка: $ACTIVE_FW_TYPE"
echo "  Версия на устройстве: $DETECTED_VER"
echo "  Версия в файле: $FIRM_VERSION"

NEED_UPDATE=true

if [ "$ACTIVE_FW_TYPE" == "Factory" ]; then
    echo "  [!] Обнаружена заводская прошивка (Factory). Обновление ОБЯЗАТЕЛЬНО."
    NEED_UPDATE=true
elif [ "$ACTIVE_FW_TYPE" == "Update" ]; then
    if [ "$DETECTED_VER" == "$FIRM_VERSION" ]; then
        echo "  [INFO] Версии совпадают ($DETECTED_VER). Обновление не требуется."
        NEED_UPDATE=false
    else
        echo "  [INFO] Версии различаются. Требуется обновление."
        NEED_UPDATE=true
    fi
else
    echo "  [WARN] Тип прошивки не определен ($ACTIVE_FW_TYPE). Принудительное обновление."
    NEED_UPDATE=true
fi

if [ "$NEED_UPDATE" = false ]; then
    echo "---------------------------------------------------"
    echo "Процедура завершена (обновление не требуется)."
    echo "---------------------------------------------------"
    
    # Запуск служб обратно
    sudo service edgeserver start
    sudo service vsmd start
    
    # Telegram Notification (Skipped)
     if [ -f "telegram_config.env" ]; then
        TAGS=$(grep -v '^#' telegram_config.env | xargs)
        if [ -n "$TAGS" ]; then export $TAGS; fi
    fi
    TS=$(date "+%d.%m.%Y, %H:%M")
    MSG="ℹ️ Прошивка уже актуальна!
Устройство: $(hostname)
Версия: $DETECTED_VER (Active: $ACTIVE_FW_TYPE)
Дата проверки: $TS
Обновление не требуется."
    python telegram_sender.py "$MSG" || true
    
    exit 2
fi

# --- ШАГ 5: ЗАМОРОЗКА WATCHDOG ---
echo -e "\n[5/7] Попытка остановки Watchdog (цикл)..."

MAX_RETRIES=3
WDT_SUCCESS=false

for (( i=1; i<=MAX_RETRIES; i++ ))
do
    echo "  --- Попытка $i из $MAX_RETRIES ---"
    
    # 1. Заморозка
    echo "  -> Отправка команды заморозки (freez)..."
    python dist/controlboard.py control freez -p "$FOUND_PORT" || true
    
    # 2. Сброс таймера в 120 (важно!)
    echo "  -> Сброс таймера в 120 сек (reset)..."
    python dist/controlboard.py control pc_wdt_reset -p "$FOUND_PORT" || true
    
    # 3. Ожидание
    echo "  -> Ожидание 3 сек..."
    sleep 3
    
    # 4. Проверка
    echo "  -> Проверка состояния..."
    WDT_OUTPUT=$(python dist/controlboard.py read pc_wdt -p "$FOUND_PORT" 2>&1 || true)
    
    if echo "$WDT_OUTPUT" | grep -q "120"; then
        echo "  [OK] УСПЕХ! Watchdog остановлен на 120 сек."
        WDT_SUCCESS=true
        break
    else
        echo "  [!] Неудача. Ответ контроллера:"
        echo "$WDT_OUTPUT" | grep "Seconds left" || echo "    (Нет корректного ответа)"
    fi
done

if [ "$WDT_SUCCESS" = false ]; then
    echo ""
    echo "---------------------------------------------------"
    echo "ОШИБКА: Не удалось остановить Watchdog за $MAX_RETRIES попыток."
    echo "Возможна нестабильная связь или сбой контроллера."
    echo "---------------------------------------------------"
    echo "[!] АВАРИЙНЫЙ ЗАПУСК СЛУЖБ..."
    sudo service edgeserver start
    sudo service vsmd start
    deactivate
    exit 1
fi

# --- ШАГ 6: ЗАПУСК ПРОШИВКИ ---
echo -e "\n[6/7] ЗАПУСК ПРОШИВКИ! Не отключайте питание!"
echo "  - Порт: $FOUND_PORT"
echo "  - Файл: $HEX_FILE"

echo "  - Версия из файла: $FIRM_VERSION"

CURRENT_DATE=$(date +%d.%m.%y)
echo "  - Дата прошивки: $CURRENT_DATE"

echo -e "\n>>> НАЧАЛО ОБНОВЛЕНИЯ <<<"
if ! python dist/controlboard.py update -p "$FOUND_PORT" -b 115200 -f "dist/$HEX_FILE" --ver_u "$FIRM_VERSION" --date_u "$CURRENT_DATE"; then
    echo "[КРИТИЧЕСКАЯ ОШИБКА] Сбой во время прошивки!"
    echo "[!] Попытка запуска служб..."
    sudo service edgeserver start
    sudo service vsmd start
    log_msg "ERROR: Flashing failed."
    exit 1
fi
log_msg "Flashing successful: $HEX_FILE ($FIRM_VERSION)"

# --- ЛОГИРОВАНИЕ УСПЕХА ---
LOG_FILE="$HOME/smalledge_fw_version"
TIMESTAMP=$(date "+%d.%m.%Y, %H:%M")
echo "$TIMESTAMP $FIRM_VERSION" >> "$LOG_FILE"
echo -e "\n  [LOG] Запись добавлена в журнал: $LOG_FILE"

# --- TELEGRAM NOTIFICATION ---
if [ -f "telegram_config.env" ]; then
    # Эспортируем переменные из файла, игнорируя комментарии
    TAGS=$(grep -v '^#' telegram_config.env | xargs)
    if [ -n "$TAGS" ]; then
        export $TAGS
    fi
fi

MSG="✅ Прошивка завершена успешно!
Устройство: $(hostname)
Версия: $FIRM_VERSION
Дата: $TIMESTAMP"

echo "  -> Отправка уведомления в Telegram..."
python telegram_sender.py "$MSG" || echo "[WARN] Не удалось запустить скрипт уведомления."


# --- ШАГ 7: ЗАВЕРШЕНИЕ ---
echo -e "\n--- ПРОШИВКА УСПЕШНО ЗАВЕРШЕНА ---"
deactivate

echo -e "\n[7/7] Запуск служб..."
sudo service edgeserver start
sudo service vsmd start
echo "Службы edgeserver и vsmd запущены."
echo "Система работает в штатном режиме."