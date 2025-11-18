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
# 1. ПРОВЕРКА ЗАПУСКА (PIPE vs TTY)
# -----------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# Если скрипт запущен через wget | bash, у него нет доступа к клавиатуре.
# Скачиваем его копию и перезапускаем в нормальном режиме.
if [ ! -t 0 ]; then
    echo "==============================================="
    echo "   ПОДГОТОВКА ЗАГРУЗЧИКА..."
    echo "==============================================="
    
    SETUP_URL="https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$BRANCH/$REPO_FOLDER/setup.sh"
    curl -s -L -o "$INSTALL_DIR/setup.sh" "$SETUP_URL"
    chmod +x "$INSTALL_DIR/setup.sh"

    # Перезапуск локальной копии с подключением терминала
    exec "$INSTALL_DIR/setup.sh" "$@" < /dev/tty
fi

# =====================================================
#  ОСНОВНОЕ ТЕЛО СКРИПТА
# =====================================================

echo "==============================================="
echo "   УПРАВЛЕНИЕ КОНТРОЛЛЕРОМ: УСТАНОВКА И ЗАПУСК"
echo "==============================================="

# -----------------------------------------------------
# 2. ПРОВЕРКА ПРАВ (SUDO + DIALOUT)
# -----------------------------------------------------
# Обновляем таймер sudo в фоне
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Проверка группы dialout
if ! groups | grep -q "dialout"; then
    echo "[!] Пользователь $USER не имеет доступа к COM-портам (нет группы 'dialout')."
    echo "    Добавление прав..."
    sudo usermod -aG dialout "$USER"
    
    echo "[OK] Права добавлены."
    echo "    Перезапуск сессии..."
    sleep 1
    
    # Магия: перезапускаем скрипт с применением новой группы "на лету"
    exec sg dialout -c "/bin/bash $0 $@"
fi
echo "[OK] Права доступа к оборудованию подтверждены."

# -----------------------------------------------------
# 3. СИНХРОНИЗАЦИЯ ФАЙЛОВ
# -----------------------------------------------------
cd "$INSTALL_DIR"
echo "[*] Загрузка актуальных версий ПО ($GITHUB_USER/$GITHUB_REPO)..."

# Получаем список файлов через API GitHub
FILES_LIST=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/contents/$REPO_FOLDER?ref=$BRANCH" | \
python3 -c "import sys, json; print('\n'.join([f['download_url'] for f in json.load(sys.stdin) if f['type'] == 'file']))")

if [ -z "$FILES_LIST" ]; then
    echo "[ОШИБКА] Не удалось получить список файлов с GitHub."
    exit 1
fi

# Скачиваем каждый файл
for url in $FILES_LIST; do
    download_file "$url" "$INSTALL_DIR"
done

chmod +x autoflash.sh
chmod +x setup.sh
echo "[OK] Файлы успешно обновлены."

# -----------------------------------------------------
# 4. ПОДГОТОВКА ОКРУЖЕНИЯ
# -----------------------------------------------------
echo "[*] Проверка системного окружения..."

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
# Установка модуля venv, если его нет
sudo apt install -y "python${PY_VER}-venv" > /dev/null 2>&1 || true

# Создание виртуального окружения
if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
# Установка pyserial (readline встроен в Linux Python)
pip install pyserial > /dev/null

echo "[OK] Система готова к работе."

# -----------------------------------------------------
# 5. ИНТЕРАКТИВНОЕ МЕНЮ
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