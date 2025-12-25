# Mass Flasher Deployment on Raspberry Pi 5

## Prerequisites

- Generic Linux System (or Raspberry Pi) with Docker installed
- Docker installed
- Git installed
- Controlboard repository cloned

## Installation Steps

1. **Update Repository**:
   Navigate to the repository and pull the latest changes from the `dev` branch.

   ```bash
   cd ~/controlboard
   git checkout dev
   git pull origin dev
   ```

2. **Navigate to Mass Flasher Directory**:

   ```bash
   cd mass_flasher
   ```

3. **Make Script Executable** (if not already):

   ```bash
   chmod +x run_docker.sh
   ```

4. **Run the Application**:
   Execute the helper script to build and start the container.

   ```bash
   ./run_docker.sh
   ```

   This script will:
   - Build the `mass-flasher` Docker image.
   - Create a `config.json` file if it doesn't exist.
   - Stop and remove any existing container named `mass_flasher_app`.
   - Start a new container with auto-restart enabled.

5. **Access the Interface**:
   Open a web browser and navigate to:
   `http://<YOUR_RPI_IP>:5000`

## Troubleshooting

- **Logs**: To check the application logs, verify the container name (default: `mass_flasher_app`) and run:

  ```bash
  docker logs -f mass_flasher_app
  ```

- **Permissions**: Ensure your user is in the `docker` group to run docker commands without sudo:

<<<<<<< Updated upstream
  ```bash
  sudo usermod -aG docker $USER
  # Log out and back in for changes to take effect
  ```
=======
1. **Настройки**: Укажите `Username`, `Password` (SSH) и `SSH Port` (обычно 2222 или 22).
2. **IP-адреса**: Введите список IP-адресов целевых устройств. Поддерживаются диапазоны:
    * `192.168.1.10` (один адрес)
    * `192.168.1.10-20` (диапазон адресов)
    * `10.8.0.50, 10.8.0.55-60` (список через запятую)
3. **Запуск**: Нажмите **Start Mass Flash**.

**Что происходит при запуске:**

* Утилита подключается к каждому устройству.
* Скачивает и запускает скрипт установки `setup.sh` из ветки `dev`.
* Запускает режим **Auto-Cleanup** (`--flash-cleanup`):
  * Если есть свежая прошивка: Устройство обновляется, очищается от временных файлов и **перезагружается**.
  * Если прошивка уже актуальна: Устройство очищается и **не перезагружается**.
  * В случае ошибки: Выводится лог, очистка не выполняется (для отладки).

### 4. Настройка Telegram (Опционально)

В интерфейсе нажмите кнопку **⚙️ Settings**.
Вы можете указать `Bot Token` и `Chat ID`. Эти настройки сохраняются локально на сервере Mass Flasher.
Если настройки заданы, устройства будут пытаться отправить отчет об обновлении в ваш Telegram чат.

## Полезные команды

Посмотреть логи работающего контейнера:

```bash
docker logs -f mass_flasher_app
```

Перезапустить/Обновить контейнер:

```bash
git pull origin dev
./run_docker.sh
```

Остановить контейнер вручную:

```bash
docker stop mass_flasher_app
docker rm mass_flasher_app
```
>>>>>>> Stashed changes
