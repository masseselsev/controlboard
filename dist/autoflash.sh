#!/bin/bash

#----------------------------------------------------------------------
# Скрипт для автоматической прошивки контроллера.
# Версия: Robust Retry (циклические попытки остановки WDT)
#----------------------------------------------------------------------

# 0. Выход при любой ошибке
set -e

echo "--- Автоматический прошивальщик контроллера ---"
echo "--- Версия Robust Retry ---"

# --- ШАГ 1: ПОИСК ФАЙЛОВ ---
echo -e "\n[1/7] Поиск необходимых файлов..."

if [ ! -f "controlboard.py" ] || [ ! -f "commands.py" ]; then
    echo "ОШИБКА: Не найдены 'controlboard.py' или 'commands.py'."
    exit 1
fi
echo "  [OK] Скрипты:  controlboard.py, commands.py"

HEX_FILES=()
while IFS= read -r -d '' file; do
    HEX_FILES+=("$(basename "$file")")
done < <(find . -maxdepth 1 -name "*.hex" -print0)

FILE_COUNT=${#HEX_FILES[@]}
HEX_FILE=""

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "ОШИБКА: .hex файл прошивки не найден."
    exit 1
elif [ "$FILE_COUNT" -eq 1 ]; then
    HEX_FILE=${HEX_FILES[0]}
    echo "  [OK] Найден один файл прошивки: $HEX_FILE"
else
    echo "  - Найдено несколько .hex файлов. Пожалуйста, выберите один:"
    for i in "${!HEX_FILES[@]}"; do
        echo "    [$((i+1))] ${HEX_FILES[$i]}"
    done
    read -p "Введите номер файла (1-$FILE_COUNT): " CHOICE
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "$FILE_COUNT" ]; then
        echo "ОШИБКА: Неверный ввод."
        exit 1
    fi
    HEX_FILE=${HEX_FILES[$((CHOICE-1))]}
    echo "  [OK] Выбрана прошивка: $HEX_FILE"
fi

# --- ШАГ 2: НАСТРОЙКА PYTHON VENV ---
echo -e "\n[2/7] Настройка Python окружения..."

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ОШИБКА: Требуется Python 3.10+."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || true

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
echo "  - Обновление pyserial..."
pip install pyserial > /dev/null

# --- ШАГ 3: ОСТАНОВКА СЛУЖБ (ВРЕМЕННО) ---
echo -e "\n[3/7] Временная остановка служб для доступа к порту..."
sudo service edgeserver stop
sudo service vsmd stop
echo "Службы остановлены. Порт свободен."

# --- ШАГ 4: ПОИСК COM-ПОРТА ---
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
    echo "[!] АВАРИЙНЫЙ ЗАПУСК СЛУЖБ ОБРАТНО..."
    sudo service edgeserver start
    sudo service vsmd start
    deactivate
    exit 1
fi

# --- ШАГ 5: ЗАМОРОЗКА WDT (С ПОВТОРАМИ) ---
echo -e "\n[5/7] Попытка остановки Watchdog (цикл)..."

MAX_RETRIES=3
WDT_SUCCESS=false

for (( i=1; i<=MAX_RETRIES; i++ ))
do
    echo "  --- Попытка $i из $MAX_RETRIES ---"
    
    # 1. Отправляем команду FREEZ
    echo "  -> Отправка команды 'control freez'..."
    # Используем || true, чтобы скрипт не вылетел, если команда вернет ошибку CRC
    python controlboard.py control freez -p "$FOUND_PORT" || true
    
    # 2. Ждем стабилизации
    echo "  -> Ожидание 3 сек..."
    sleep 3
    
    # 3. Проверяем результат
    echo "  -> Проверка WDT..."
    WDT_OUTPUT=$(python controlboard.py read pc_wdt -p "$FOUND_PORT" 2>&1 || true)
    
    if echo "$WDT_OUTPUT" | grep -q "120"; then
        echo "  [OK] УСПЕХ! Watchdog остановлен на 120 сек."
        WDT_SUCCESS=true
        break
    else
        echo "  [!] Неудача. Ответ контроллера:"
        # Выводим только строку со значением, чтобы не спамить
        echo "$WDT_OUTPUT" | grep "Seconds left" || echo "    (Нет корректного ответа)"
    fi
done

# Если после всех попыток успеха нет - выходим
if [ "$WDT_SUCCESS" = false ]; then
    echo ""
    echo "---------------------------------------------------"
    echo "ОШИБКА: Не удалось остановить Watchdog за $MAX_RETRIES попыток."
    echo "Возможна нестабильная связь или сбой контроллера."
    echo "---------------------------------------------------"
    echo "[!] АВАРИЙНЫЙ ЗАПУСК СЛУЖБ ОБРАТНО..."
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
    echo "  - Обнаружена версия: $FIRM_VERSION"
fi

CURRENT_DATE=$(date +%d.%m.%y)
echo "  - Дата прошивки: $CURRENT_DATE"

echo -e "\n>>> START UPDATE <<<"
if ! python controlboard.py update -p "$FOUND_PORT" -f "$HEX_FILE" --ver_u "$FIRM_VERSION" --date_u "$CURRENT_DATE"; then
    echo "[FATAL ERROR] Ошибка во время прошивки!"
    echo "[!] Попытка запуска служб..."
    sudo service edgeserver start
    sudo service vsmd start
    exit 1
fi

# --- ШАГ 7: ЗАВЕРШЕНИЕ ---
echo -e "\n--- ПРОШИВКА УСПЕШНО ЗАВЕРШЕНА ---"
deactivate

echo -e "\n[7/7] Запуск служб..."
sudo service edgeserver start
sudo service vsmd start
echo "Службы edgeserver и vsmd запущены."
echo "Система в рабочем режиме."