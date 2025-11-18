#!/bin/bash

#----------------------------------------------------------------------
# Скрипт для автоматической прошивки контроллера.
# Версия: Final (Sudo Keep-Alive + Smart Port Detection + Auto-Service)
#----------------------------------------------------------------------

# 0. Выход при любой ошибке
set -e

# ==============================================================================
# [БЛОК 0] SUDO KEEP-ALIVE (МАГИЯ)
# Запрашиваем пароль один раз в начале и поддерживаем права активными
# ==============================================================================
echo "--- Автоматический прошивальщик контроллера ---"

# Проверяем, можем ли мы выполнить sudo. Если нет - запрашиваем пароль.
sudo -v

# Запускаем фоновый процесс, который обновляет таймер sudo каждые 60 сек
# Это гарантирует, что пароль не будет запрошен снова, даже если прошивка идет долго.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
# ==============================================================================


# --- ШАГ 1: ПОИСК ФАЙЛОВ ---
echo -e "\n[1/8] Поиск необходимых файлов..."

# Проверка, что скрипты на месте
if [ ! -f "controlboard.py" ] || [ ! -f "commands.py" ]; then
    echo "ОШИБКА: Не найдены 'controlboard.py' или 'commands.py'."
    echo "Убедитесь, что они лежат в той же папке."
    exit 1
fi
echo "  [OK] Скрипты:  controlboard.py, commands.py"

# Ищем .hex файлы и заносим в массив (безопасно)
HEX_FILES=()
while IFS= read -r -d '' file; do
    HEX_FILES+=("$(basename "$file")")
done < <(find . -maxdepth 1 -name "*.hex" -print0)

FILE_COUNT=${#HEX_FILES[@]}
HEX_FILE=""

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "ОШИБКА: .hex файл прошивки не найден в этой папке."
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


# --- ШАГ 2: НАСТРОЙКА PYTHON VENV (ПАКЕТ) ---
echo -e "\n[2/8] Настройка Python окружения (venv)..."

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ОШИБКА: 'controlboard.py' требует Python 3.10 или новее."
    python3 --version
    exit 1
fi

# Установка venv пакета (используем sudo, пароль уже введен в начале)
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  - Проверка/установка пакета python${PY_VER}-venv..."
sudo apt install -y "python${PY_VER}-venv" > /dev/null


# --- ШАГ 3: VENV И ЗАВИСИМОСТИ (PIP) ---
echo -e "\n[3/8] Установка зависимостей в venv..."

if [ ! -d "env" ]; then
    echo "  - Создание venv..."
    python3 -m venv env
else
    echo "  - Окружение 'env' уже существует."
fi

source env/bin/activate
echo "  - Установка зависимости (pyserial)..."
pip install pyserial > /dev/null


# --- ШАГ 4: ПОИСК COM-ПОРТА ---
echo -e "\n[4/8] Поиск контроллера на COM-портах..."
FOUND_PORT=""
set +e # Временно отключаем выход по ошибке
for port in /dev/ttyUSB{0,1,2,3,4}; do
    # Если порта физически нет, пропускаем
    [ -e "$port" ] || continue
    
    echo -n "  - Проверка $port... "
    # Захватываем вывод и ищем успешный ответ
    OUTPUT=$(python controlboard.py read version_request -p "$port" 2>&1)
    
    if echo "$OUTPUT" | grep -q ">>> Version is right!!!"; then
        FOUND_PORT="$port"
        echo "OK! Контроллер найден."
        break
    else
        echo "Нет ответа (или не тот порт)."
    fi
done
set -e

if [ -z "$FOUND_PORT" ]; then
    echo "ОШИБКА: Не удалось найти контроллер ни на одном из портов ttyUSB(0-4)."
    deactivate
    exit 1
fi


# --- ШАГ 5: ЗАМОРОЗКА WDT ---
echo -e "\n[5/8] Остановка Watchdog (control freez) на $FOUND_PORT..."
python controlboard.py control freez -p "$FOUND_PORT"


# --- ШАГ 6: ПРОВЕРКА WDT ---
echo -e "\n[6/8] Проверка статуса Watchdog..."
echo "  - Ожидание 5 секунд для стабилизации..."
sleep 5
echo "  - Чтение таймера WDT..."
WDT_OUTPUT=$(python controlboard.py read pc_wdt -p "$FOUND_PORT")
echo "${WDT_OUTPUT}"

if ! echo "${WDT_OUTPUT}" | grep -q "120"; then
    echo "ОШИБКА: Не удалось остановить Watchdog."
    deactivate
    exit 1
fi
echo "  [OK] Watchdog успешно остановлен (120)."


# --- ШАГ 7: ОСТАНОВКА СЛУЖБ ---
echo -e "\n[7/8] Остановка служб..."
sudo service edgeserver stop
sudo service vsmd stop
echo "Службы edgeserver и vsmd остановлены."


# --- ШАГ 8: ЗАПУСК ПРОШИВКИ ---
echo -e "\n[8/8] ЗАПУСК ПРОШИВКИ! Не отключайте питание!"
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
python controlboard.py update -p "$FOUND_PORT" -f "$HEX_FILE" --ver_u "$FIRM_VERSION" --date_u "$CURRENT_DATE"


# --- ЗАВЕРШЕНИЕ ---
echo -e "\n--- ПРОШИВКА УСПЕШНО ЗАВЕРШЕНА ---"
deactivate
echo "Окружение venv деактивировано."

echo -e "\n[+] Запуск служб..."
sudo service edgeserver start
sudo service vsmd start
echo "Службы edgeserver и vsmd запущены."
echo "Система в рабочем режиме."