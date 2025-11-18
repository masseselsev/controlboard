#!/bin/bash

# ================= КОНФИГУРАЦИЯ =================
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="dist"
BRANCH="main"
INSTALL_DIR="$HOME/controlboard"
# ================================================

set -e

# Функция для скачивания файла
download_file() {
    local url=$1
    local dest_dir=$2
    local filename=$(basename "$url")
    
    echo "  -> Скачивание: $filename"
    curl -s -L -o "$dest_dir/$filename" "$url"
}

# -----------------------------------------------------
# 1. ПЕРВИЧНАЯ ИНИЦИАЛИЗАЦИЯ (ЕСЛИ ЗАПУСК ИЗ WGET)
# -----------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# Если stdin - не терминал (запуск через pipe | bash),
# нам нужно сначала скачать самого себя, чтобы иметь возможность перезапуститься.
if [ ! -t 0 ]; then
    echo "==============================================="
    echo "   ПОДГОТОВКА ЗАГРУЗЧИКА..."
    echo "==============================================="
    
    # Скачиваем только setup.sh
    SETUP_URL="https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$BRANCH/$REPO_FOLDER/setup.sh"
    curl -s -L -o "$INSTALL_DIR/setup.sh" "$SETUP_URL"
    chmod +x "$INSTALL_DIR/setup.sh"

    # Передаем управление локальной копии с подключением клавиатуры
    exec "$INSTALL_DIR/setup.sh" "$@" < /dev/tty
fi

# =====================================================
#  ДАЛЕЕ СКРИПТ РАБОТАЕТ В ОБЫЧНОМ РЕЖИМЕ
# =====================================================

echo "==============================================="
echo "   CONTROL BOARD: SETUP & LAUNCHER"
echo "==============================================="

# -----------------------------------------------------
# 2. ПРОВЕРКА ПРАВ
# -----------------------------------------------------
# Sudo Keep-alive
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Проверка Dialout
if ! groups | grep -q "dialout"; then
    echo "[!] Текущий пользователь ($USER) НЕ состоит в группе 'dialout'."
    echo "    Добавляем и перезапускаем..."
    sudo usermod -aG dialout "$USER"
    sleep 1
    exec sg dialout -c "/bin/bash $0 $@"
fi

# -----------------------------------------------------
# 3. СКАЧИВАНИЕ ФАЙЛОВ (ОДИН РАЗ)
# -----------------------------------------------------
# Мы дошли сюда только если у нас есть TTY и права Dialout.
# Теперь можно качать полный пакет.

cd "$INSTALL_DIR"
echo "[*] Синхронизация файлов с GitHub ($GITHUB_USER/$GITHUB_REPO)..."

FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ERROR] Не удалось получить список файлов."
    exit 1
fi

for url in $FILES_LIST; do
    download_file "$url" "$INSTALL_DIR"
done

chmod +x autoflash.sh
chmod +x setup.sh
echo "[OK] Все файлы обновлены."

# -----------------------------------------------------
# 4. НАСТРОЙКА ОКРУЖЕНИЯ
# -----------------------------------------------------
echo "[*] Настройка окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || true

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
# Только pyserial, readline встроен в Linux
pip install pyserial > /dev/null

echo "[OK] Система готова."

# -----------------------------------------------------
# 5. МЕНЮ
# -----------------------------------------------------
while true; do
    echo ""
    echo "=========================================="
    echo "   МЕНЮ УПРАВЛЕНИЯ КОНТРОЛЛЕРОМ"
    echo "=========================================="
    echo "1) Запустить Консоль Управления (app.py)"
    echo "2) Запустить Прошивку (autoflash.sh)"
    echo "3) Выход"
    echo ""
    
    read -p "Выберите действие (1-3): " choice

    case $choice in
        1)
            echo "Запуск app.py..."
            python app.py
            ;;
        2)
            echo "Запуск autoflash.sh..."
            ./autoflash.sh
            echo "Нажмите Enter, чтобы вернуться в меню..."
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