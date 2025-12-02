#!/bin/bash

# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="15"
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
    echo "$(date '+%Y-%m-%d %H:%M:%S') [FLASH] $msg" >> "$GLOBAL_LOG"
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

if [ ! -f "controlboard.py" ] || [ ! -f "commands.py" ]; then
    echo "ОШИБКА: Не найдены файлы 'controlboard.py' или 'commands.py'."
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
done < <(find . -maxdepth 1 -name "*.hex" -print0 | sort -z)

FILE_COUNT=${#HEX_FILES[@]}
HEX_FILE=""

if [ "$FILE_COUNT" -eq 0 ]; then
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
pip install pyserial > /dev/null

# --- ШАГ 3: ОСТАНОВКА СЛУЖБ ---
echo -e "\n[3/7] Временная остановка служб для доступа к порту..."
sudo service edgeserver stop
sudo service vsmd stop
echo "Службы остановлены. Порт свободен."

# --- ШАГ 4: ПОИСК ПОРТА ---
echo -e "\n[4/7] Поиск контроллера на COM-портах..."
FOUND_PORT=""
set +e
for port in /dev/ttyUSB{0,1,2,3,4}; do
    [ -e "$port" ] || continue
    echo -n "  - Проверка $port... "
    OUTPUT=$(python controlboard.py read version_request -p "$port" 2>&1)
    if echo "$OUTPUT" | grep -q ">>> Version is right!!!"; then
        FOUND_PORT="$port"
        echo "OK! Контроллер найден."
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

# --- ШАГ 5: ЗАМОРОЗКА WATCHDOG ---
echo -e "\n[5/7] Попытка остановки Watchdog (цикл)..."

MAX_RETRIES=3
WDT_SUCCESS=false

for (( i=1; i<=MAX_RETRIES; i++ ))
do
    echo "  --- Попытка $i из $MAX_RETRIES ---"
    
    # 1. Заморозка
    echo "  -> Отправка команды заморозки (freez)..."
    python controlboard.py control freez -p "$FOUND_PORT" || true
    
    # 2. Сброс таймера в 120 (важно!)
    echo "  -> Сброс таймера в 120 сек (reset)..."
    python controlboard.py control pc_wdt_reset -p "$FOUND_PORT" || true
    
    # 3. Ожидание
    echo "  -> Ожидание 3 сек..."
    sleep 3
    
    # 4. Проверка
    echo "  -> Проверка состояния..."
    WDT_OUTPUT=$(python controlboard.py read pc_wdt -p "$FOUND_PORT" 2>&1 || true)
    
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

FIRM_VERSION="00.00.00"
if [[ $HEX_FILE =~ V([0-9]{2}\.[0-9]{2}\.[0-9]{2}) ]]; then
    FIRM_VERSION=${BASH_REMATCH[1]}
    echo "  - Версия из файла: $FIRM_VERSION"
fi

CURRENT_DATE=$(date +%d.%m.%y)
echo "  - Дата прошивки: $CURRENT_DATE"

echo -e "\n>>> НАЧАЛО ОБНОВЛЕНИЯ <<<"
if ! python controlboard.py update -p "$FOUND_PORT" -f "$HEX_FILE" --ver_u "$FIRM_VERSION" --date_u "$CURRENT_DATE"; then
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

# --- ШАГ 7: ЗАВЕРШЕНИЕ ---
echo -e "\n--- ПРОШИВКА УСПЕШНО ЗАВЕРШЕНА ---"
deactivate

echo -e "\n[7/7] Запуск служб..."
sudo service edgeserver start
sudo service vsmd start
echo "Службы edgeserver и vsmd запущены."
echo "Система работает в штатном режиме."