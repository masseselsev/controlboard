#!/bin/bash

# ================= КОНФИГУРАЦИЯ =================
GITHUB_USER="masseselsev"
GITHUB_REPO="controlboard"
REPO_FOLDER="dist"
BRANCH="main"
INSTALL_DIR="$HOME/controlboard"
# ================================================

set -e

# -----------------------------------------------------
# 1. ПОДГОТОВКА И СКАЧИВАНИЕ (ЭТО РАБОТАЕТ ВСЕГДА)
# -----------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# Мы скачиваем файлы ДО проверки терминала, чтобы было что запускать
echo "[*] Синхронизация файлов с GitHub в $INSTALL_DIR..."

# Получаем список файлов
FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ERROR] Не удалось получить список файлов."
    exit 1
fi

# Скачиваем файлы
for url in $FILES_LIST; do
    filename=$(basename "$url")
    # Скачиваем тихо, чтобы не засорять вывод
    curl -s -L -o "$INSTALL_DIR/$filename" "$url"
done

chmod +x "$INSTALL_DIR/autoflash.sh"
chmod +x "$INSTALL_DIR/setup.sh"

# -----------------------------------------------------
# 2. МАГИЯ ПЕРЕЗАПУСКА (ВЫХОД ИЗ ТРУБЫ)
# -----------------------------------------------------
# Если скрипт запущен через pipe (wget | bash), то дескриптор 0 (stdin) не является терминалом.
# Мы должны перезапустить локальную копию, подключив к ней реальный TTY.

if [ ! -t 0 ]; then
    echo "==============================================="
    echo "   ПЕРЕХОД В ИНТЕРАКТИВНЫЙ РЕЖИМ..."
    echo "==============================================="
    # exec заменяет текущий процесс новым.
    # < /dev/tty принудительно подключает клавиатуру к новому процессу.
    exec "$INSTALL_DIR/setup.sh" "$@" < /dev/tty
fi

# =====================================================
#  С ЭТОГО МОМЕНТА МЫ ГАРАНТИРОВАННО РАБОТАЕМ ИЗ ФАЙЛА
#  И ИМЕЕМ ДОСТУП К КЛАВИАТУРЕ
# =====================================================

echo "==============================================="
echo "   CONTROL BOARD: SETUP & LAUNCHER"
echo "==============================================="

# -----------------------------------------------------
# 3. ПРОВЕРКА SUDO
# -----------------------------------------------------
echo "[*] Проверка прав суперпользователя..."
sudo -v
# Keep-alive для sudo
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# -----------------------------------------------------
# 4. ПРОВЕРКА DIALOUT
# -----------------------------------------------------
if ! groups | grep -q "dialout"; then
    echo "[!] Текущий пользователь ($USER) НЕ состоит в группе 'dialout'."
    echo "    Добавляем..."
    sudo usermod -aG dialout "$USER"
    
    echo "[OK] Добавлен. Перезапуск с новыми правами..."
    sleep 1
    # Перезапускаем этот же скрипт ($0), но через sg для применения группы
    exec sg dialout -c "/bin/bash $0 $@"
fi
echo "[OK] Права доступа к COM-портам подтверждены."

# -----------------------------------------------------
# 5. НАСТРОЙКА ОКРУЖЕНИЯ
# -----------------------------------------------------
cd "$INSTALL_DIR"
echo "[*] Настройка окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
# Ставим venv
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || true

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
# Устанавливаем ТОЛЬКО pyserial, readline встроен в Linux
pip install pyserial > /dev/null

echo "[OK] Система готова."

# -----------------------------------------------------
# 6. ГЛАВНОЕ МЕНЮ
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
    
    # Теперь тут не нужны костыли < /dev/tty, так как мы уже переключились глобально
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