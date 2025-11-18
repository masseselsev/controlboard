#!/bin/bash

# ================= КОНФИГУРАЦИЯ =================
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="dist"      # Папка в репозитории
BRANCH="main"
INSTALL_DIR="$HOME/controlboard"
# ================================================

set -e

echo "==============================================="
echo "   CONTROL BOARD: SETUP & LAUNCHER"
echo "==============================================="

# -----------------------------------------------------
# 1. ПРОВЕРКА SUDO (Keep-Alive)
# -----------------------------------------------------
echo "[*] Проверка прав суперпользователя..."
sudo -v
# Обновляем таймер sudo в фоне
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# -----------------------------------------------------
# 2. ПРОВЕРКА DIALOUT С "ГОРЯЧИМ" ПРИМЕНЕНИЕМ
# -----------------------------------------------------
if ! groups | grep -q "dialout"; then
    echo "[!] Текущий пользователь ($USER) НЕ состоит в группе 'dialout'."
    echo "    Добавляем пользователя..."
    sudo usermod -aG dialout "$USER"
    
    echo "[OK] Пользователь добавлен."
    echo "    Перезапуск скрипта с новыми правами..."
    sleep 2
    
    # Перезапускаем скрипт
    exec sg dialout -c "/bin/bash $0 $@"
fi
echo "[OK] Права доступа к COM-портам подтверждены."

# -----------------------------------------------------
# 3. ПОДГОТОВКА ПАПКИ И СКАЧИВАНИЕ ФАЙЛОВ
# -----------------------------------------------------
echo "[*] Подготовка рабочей директории: $INSTALL_DIR"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

echo "[*] Синхронизация файлов с GitHub ($GITHUB_USER/$GITHUB_REPO/$REPO_FOLDER)..."

# Скачиваем список файлов и сами файлы
FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ERROR] Не удалось получить список файлов. Проверьте настройки репозитория."
    exit 1
fi

for url in $FILES_LIST; do
    filename=$(basename "$url")
    echo -n "    Downloading $filename ... "
    curl -s -L -O "$url"
    echo "OK"
done

chmod +x autoflash.sh
echo "[OK] Все файлы обновлены."

# -----------------------------------------------------
# 4. НАСТРОЙКА ОКРУЖЕНИЯ (VENV)
# -----------------------------------------------------
echo "[*] Проверка системных зависимостей..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "    Detected Python $PY_VER"

# Ставим venv пакет
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || echo "    (Пакет venv уже установлен или не найден, продолжаем)"

if [ ! -d "env" ]; then
    echo "    Создание виртуального окружения (env)..."
    python3 -m venv env
else
    echo "    Виртуальное окружение уже существует."
fi

echo "    Обновление библиотек (pyserial)..."
source env/bin/activate

# === ИСПРАВЛЕНИЕ ЗДЕСЬ ===
# Убрали 'readline', так как он встроен в Python на Linux
pip install pyserial > /dev/null 
# =========================

echo "[OK] Окружение готово."

# -----------------------------------------------------
# 5. ГЛАВНОЕ МЕНЮ
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
    read -p "Выберите действие (1-3): " choice < /dev/tty

    case $choice in
        1)
            echo "Запуск app.py..."
            python app.py
            ;;
        2)
            echo "Запуск autoflash.sh..."
            ./autoflash.sh
            echo "Нажмите Enter, чтобы вернуться в меню..."
            read < /dev/tty
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