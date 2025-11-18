#!/bin/bash

# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="7"
# ==================================================

# ================= КОНФИГУРАЦИЯ =================
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="dist"
BRANCH="main"
INSTALL_DIR="$HOME/controlboard"
# ================================================

set -e

# -----------------------------------------------------
# 0. ВЫВОД ВЕРСИИ (ТОЛЬКО ОДИН РАЗ)
# -----------------------------------------------------
if [ -z "$CB_SETUP_RUNNING" ]; then
    echo "--------------------------------------------------"
    echo "   Setup Script Version: $SCRIPT_VERSION"
    echo "--------------------------------------------------"
    export CB_SETUP_RUNNING="true"
fi

# -----------------------------------------------------
# 1. АВТО-КОНФИГУРАЦИЯ ИЗ URL
# -----------------------------------------------------
if [ -n "$1" ]; then
    INPUT_URL="$1"
    if [[ "$INPUT_URL" =~ https://raw.githubusercontent.com/([^/]+)/([^/]+)/([^/]+)/(.+) ]]; then
        GITHUB_USER="${BASH_REMATCH[1]}"
        GITHUB_REPO="${BASH_REMATCH[2]}"
        BRANCH="${BASH_REMATCH[3]}"
        FULL_PATH="${BASH_REMATCH[4]}"
        REPO_FOLDER=$(dirname "$FULL_PATH")
    fi
fi

# Функция для скачивания файла (ИСПРАВЛЕННАЯ)
download_file() {
    local url=$1
    local dest_dir=$2
    
    # 1. Убираем всё после знака '?' (параметры кеша)
    local clean_url="${url%%\?*}"
    
    # 2. Теперь basename вернет чистое имя файла
    local filename=$(basename "$clean_url")
    
    echo "  -> Скачивание: $filename"
    # 3. Сохраняем под чистым именем, но качаем по полной ссылке (с анти-кешем)
    curl -s -L -o "$dest_dir/$filename" "$url"
}

# -----------------------------------------------------
# 2. ПОДГОТОВКА ЗАГРУЗЧИКА
# -----------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

if [ ! -t 0 ]; then
    echo "==============================================="
    echo "   ПОДГОТОВКА ЗАГРУЗЧИКА..."
    echo "==============================================="
    
    # Добавляем анти-кеш
    CACHE_BUST="?t=$(date +%s)"
    SETUP_URL="https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$BRANCH/$REPO_FOLDER/setup.sh$CACHE_BUST"
    
    # Используем нашу умную функцию download_file даже здесь, 
    # но вручную, так как она еще не определена в старой версии, если мы обновляемся.
    # Поэтому тут используем curl напрямую, но правильно именуем файл.
    
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
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

if ! groups | grep -q "dialout"; then
    echo "[!] Пользователь $USER не имеет доступа к COM-портам."
    echo "    Добавление прав..."
    sudo usermod -aG dialout "$USER"
    
    echo "[OK] Права добавлены. Перезапуск..."
    sleep 1
    
    exec sg dialout -c "CB_SETUP_RUNNING=true /bin/bash $0 $1"
fi
echo "[OK] Права доступа подтверждены."

# -----------------------------------------------------
# 4. СИНХРОНИЗАЦИЯ ФАЙЛОВ
# -----------------------------------------------------
cd "$INSTALL_DIR"

echo "[*] Синхронизация с GitHub:"
echo "    Источник: $GITHUB_USER/$GITHUB_REPO (Ветка: $BRANCH)"

# Получаем список. Добавляем анти-кеш к самому запросу API (если возможно) или просто надеемся на свежесть.
# В raw ссылках внутри списка параметры ?t=... пока отсутствуют.
FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH&t=$(date +%s)" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ОШИБКА] Не удалось получить список файлов."
    exit 1
fi

# Удаляем старые файлы с "кривыми" именами (если есть), чтобы не мусорить
rm -f *\?t\=*

for url in $FILES_LIST; do
    # Добавляем анти-кеш к каждой ссылке
    download_file "$url?t=$(date +%s)" "$INSTALL_DIR"
done

chmod +x autoflash.sh
chmod +x setup.sh
echo "[OK] Файлы успешно обновлены."

# -----------------------------------------------------
# 5. ПОДГОТОВКА ОКРУЖЕНИЯ
# -----------------------------------------------------
echo "[*] Проверка системного окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || true

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
pip install pyserial > /dev/null

echo "[OK] Система готова к работе."

# -----------------------------------------------------
# 6. ИНТЕРАКТИВНОЕ МЕНЮ
# -----------------------------------------------------
while true; do
    echo ""
    echo "=========================================="
    echo "   МЕНЮ УПРАВЛЕНИЯ"
    echo "=========================================="
    echo "1) Консоль управления (app.py)"
    echo "2) Прошивка контроллера (autoflash.sh)"
    echo "3) Выход"
    echo ""
    
    read -p "Ваш выбор (1-3): " choice

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
        *)
            echo "Неверный выбор."
            ;;
    esac
done