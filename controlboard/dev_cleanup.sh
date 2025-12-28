#!/bin/bash

# ==================================================
# dev_cleanup.sh
# Скрипт для полной очистки системы от изменений,
# внесенных setup.sh и autoflash.sh.
# ==================================================

# ================= ВЕРСИЯ СКРИПТА =================
SCRIPT_VERSION="4"
# ==================================================

# Конфигурация
INSTALL_DIR="$HOME/controlboard"
STATE_FILE="$INSTALL_DIR/dev_init.txt"
GLOBAL_LOG="$HOME/controlboard.log"

# --- ЛОГИРОВАНИЕ ---
log_msg() {
    local msg="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [CLEANUP] $msg" >> "$GLOBAL_LOG"
    echo "[CLEANUP] $msg"
}

# --- ФУНКЦИЯ SUDO ---
sudo_smart() {
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    if echo "admin" | sudo -S -v 2>/dev/null; then
        return 0
    fi
    sudo -v
}

# --- ПРОВЕРКИ ---
if [ ! -d "$INSTALL_DIR" ]; then
    echo "[WARN] Директория $INSTALL_DIR не найдена. Нечего очищать."
    exit 0
fi

echo "--- Cleanup Script (v$SCRIPT_VERSION) ---"
log_msg "--- Starting cleanup process (v$SCRIPT_VERSION) ---"

# 1. Чтение файла состояния
if [ ! -f "$STATE_FILE" ]; then
    log_msg "WARNING: State file $STATE_FILE not found. Only directory removal will be performed."
else
    log_msg "Reading state file: $STATE_FILE"
    
    # Читаем файл в массив, чтобы не держать его открытым при удалении
    mapfile -t LINES < "$STATE_FILE"
    
    # Обрабатываем в обратном порядке (LIFO)
    for (( idx=${#LINES[@]}-1 ; idx>=0 ; idx-- )) ; do
        line="${LINES[idx]}"
        type="${line%%:*}"
        value="${line#*:}"
        
        case "$type" in
            PACKAGE)
                log_msg "Removing package: $value"
                sudo_smart
                sudo apt remove -y "$value" >> "$GLOBAL_LOG" 2>&1
                sudo apt autoremove -y >> "$GLOBAL_LOG" 2>&1
                ;;
            GROUP_USER)
                # value format: group:user
                group="${value%%:*}"
                user="${value#*:}"
                log_msg "Removing user $user from group $group"
                sudo_smart
                sudo deluser "$user" "$group" >> "$GLOBAL_LOG" 2>&1
                ;;
            DIR)
                # Директории удалим в конце
                log_msg "Directory marked for removal: $value"
                ;;
            *)
                log_msg "Unknown entry type: $type"
                ;;
        esac
    done
fi

# 2. Удаление директории проекта
log_msg "Removing project directory: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"

log_msg "Cleanup complete. System should be clean."
log_msg "Log file remains at: $GLOBAL_LOG"
echo "[INFO] Done."
