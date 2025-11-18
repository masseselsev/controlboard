#!/usr/bin/env python3

"""
Интерактивное приложение (REPL) для управления контроллером
на базе controlboard.py и commands.py.
"""

import sys
import time
import binascii
import re
import struct
import serial
import readline  # Добавляет историю команд и навигацию по стрелкам

# --- Импортируем словари команд ---
try:
    import commands
except ImportError:
    print("[ERROR] Не найден файл commands.py. Он должен быть в той же папке.")
    sys.exit(1)

# --- Блок, скопированный из controlboard.py (Логика Modbus) ---

# Таблицы CRC16
table_crc_hi = [
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
   0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
   0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1,
   0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1,
   0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40,
   0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1,
   0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40,
   0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
   0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
   0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
   0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40,
   0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1,
   0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
   0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
   0x80, 0x41, 0x00, 0xC1, 0x81, 0x40
]
table_crc_lo = [
   0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06,
   0x07, 0xC7, 0x05, 0xC5, 0xC4, 0x04, 0xCC, 0x0C, 0x0D, 0xCD,
   0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09,
   0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A,
   0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC, 0x14, 0xD4,
   0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
   0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3,
   0xF2, 0x32, 0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4,
   0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A,
   0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38, 0x28, 0xE8, 0xE9, 0x29,
   0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF, 0x2D, 0xED,
   0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
   0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60,
   0x61, 0xA1, 0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67,
   0xA5, 0x65, 0x64, 0xA4, 0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F,
   0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68,
   0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA, 0xBE, 0x7E,
   0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
   0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71,
   0x70, 0xB0, 0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92,
   0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C,
   0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B,
   0x99, 0x59, 0x58, 0x98, 0x88, 0x48, 0x49, 0x89, 0x4B, 0x8B,
   0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
   0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42,
   0x43, 0x83, 0x41, 0x81, 0x80, 0x40
]

def crc16(buffer):
    crc_hi = 0xFF
    crc_lo = 0xFF
    for byte in buffer:
        i = crc_hi ^ byte
        crc_hi = crc_lo ^ table_crc_hi[i]
        crc_lo = table_crc_lo[i]
    return (crc_hi << 8) | crc_lo

def valid_crc16(response: bytes) -> bool:
    if len(response) < 2:
        return False
    response_crc = int.from_bytes(response[-2:], byteorder='big')
    crc = crc16(response[:-2])
    return response_crc == crc

def build_modbus_cmd(
        modbus_dict: commands.ModbusDict,
        override_address: int | None = None,
        override_function: int | None = None,
        override_register: int | None = None,
        override_value: int | None = None
    ) -> bytes:
    address     = override_address if override_address is not None else modbus_dict["address"]
    function    = override_function if override_function is not None else modbus_dict["function"]
    register    = override_register if override_register is not None else modbus_dict["register"]
    value       = override_value if override_value is not None else modbus_dict["value"]
    value       = value & 0xFFFF

    address     = min(max(address, 0), 0xFF)
    function    = min(max(function, 0), 0xFF)
    register    = min(max(register, 0), 0xFFFF)
    value       = min(max(value, 0), 0xFFFF)

    raw_cmd = (
        address.to_bytes(1,"big") +
        function.to_bytes(1,"big") +
        register.to_bytes(2,"big") +
        value.to_bytes(2,"big")
    )
    crc = crc16(raw_cmd)
    return raw_cmd + crc.to_bytes(2,"big")

def send_and_get(
        cmd_array,
        expected_bytes: int,
        ser,
        ov_addr: int | None = None,
        ov_func: int | None = None,
        ov_reg: int | None = None,
        ov_value: int | None = None
    ) -> bytes:

    send_cmd = build_modbus_cmd(
                    cmd_array["modbus"],
                    override_address=ov_addr if ov_addr is not None else None,
                    override_function=ov_func if ov_func is not None else None,
                    override_register=ov_reg if ov_reg is not None else None,
                    override_value=ov_value if ov_value is not None else None
                )

    send_hex = binascii.hexlify(send_cmd).decode('utf-8').upper()
    send_hex_f = " ".join(send_hex[i:i+2] for i in range(0, len(send_hex), 2))
    print(f'> Send bytes: {send_hex_f}')

    ser.write(send_cmd)
    response = ser.read(expected_bytes) # ВАЖНО: читаем ожидаемое кол-во

    response_hex = binascii.hexlify(response).decode('utf-8').upper()
    response_hex_f = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
    print(f'> Received: {response_hex_f}')

    if not response:
        raise Exception("Timeout: No data received from device.")

    if not valid_crc16(response):
        raise Exception(f'Invalid CRC16! Received: {response_hex_f}')
    
    if len(response) < 5:
        raise Exception(f"Invalid response length: {len(response)} (expected at least 5 bytes)")
    
    if response[0] != cmd_array["modbus"]["address"]:
        raise Exception(f"Unexpected device address: {hex(response[0])} (expected {hex(cmd_array['modbus']['address'])})")
    
    if not (response[1] & cmd_array["modbus"]["function"]):
         raise Exception(f"Device returned an error function. Code: {hex(response[1])}")

    if response[1] & 0x80:
        raise Exception(f"Device returned an error. Code: {hex(response[2])}")

    if len(response) < expected_bytes:
        print(f"[WARNING] Short response: got {len(response)}, expected {expected_bytes}")
    
    return response

# --- Копируем функции-обработчики из controlboard.py ---
# Мы не будем копировать *..._with_serial, так как порт будет открыт постоянно.
# Мы будем вызывать 'func_read', 'func_write', 'func_control' напрямую.
# ВАЖНО: Этот код зависит от `controlboard.py` и `commands.py`
# Я скопирую сюда только 'func_read', 'func_write', 'func_control' для примера
# В идеале, их нужно импортировать из controlboard, если он оформлен как модуль
# Но проще скопировать, т.к. они зависят от global `commands`
# ...
# [ОШИБКА] Копирование десятков функций (func_read, func_write...) вручную неэффективно.
# ЛУЧШИЙ ПОДХОД: Мы импортируем controlboard.py КАК МОДУЛЬ
# и будем вызывать его функции.

try:
    import controlboard
except ImportError:
    print("[ERROR] Не найден файл controlboard.py. Он должен быть в той же папке.")
    sys.exit(1)


# --- Новая логика REPL ---

def print_help():
    """Показывает список доступных команд"""
    print("\n--- Доступные команды ---")
    print("\n[ Тип: read ]")
    for cmd, info in commands.cmd_read_array.items():
        print(f"  {cmd:20} : {info['description']}")
    
    print("\n[ Тип: write (используйте 'write <cmd> <value>') ]")
    for cmd, info in commands.cmd_write_array.items():
        print(f"  {cmd:20} : {info['description']}")

    print("\n[ Тип: control ]")
    for cmd, info in commands.cmd_control_array.items():
        print(f"  {cmd:20} : {info['description']}")
    
    print("\n--- Системные команды ---")
    print("  help                 : Показать это сообщение")
    print("  exit                 : Выйти из программы")
    print("-" * 25)

def main_loop(ser):
    """Главный цикл обработки команд"""
    print("\nВведите 'help' для списка команд, 'exit' для выхода.")
    
    while True:
        try:
            # Используем input() для получения команды
            raw_input = input(f"\ncontrol@{ser.port}> ")
            if not raw_input.strip():
                continue

            parts = raw_input.split()
            cmd_type = parts[0].lower()
            
            if cmd_type == "exit":
                print("Завершение работы...")
                break
            
            if cmd_type == "help":
                print_help()
                continue
            
            if len(parts) < 2:
                print(f"[ERROR] Неверный формат. Укажите тип и команду, например: 'read version_request'")
                continue

            cmd_name = parts[1]
            value = parts[2] if len(parts) > 2 else None
            
            # --- Маршрутизация команды ---
            if cmd_type == "read":
                if cmd_name in commands.cmd_read_array:
                    # Вызываем оригинальную функцию из controlboard
                    controlboard.func_read(cmd_name, ser)
                else:
                    print(f"[ERROR] Неизвестная команда 'read {cmd_name}'")
            
            elif cmd_type == "write":
                if cmd_name in commands.cmd_write_array:
                    if value is None and cmd_name not in ["rtc", "heat1_on", "heat2_on"]:
                        print(f"[ERROR] Команда 'write {cmd_name}' требует <value>.")
                    else:
                        controlboard.func_write(cmd_name, ser, value)
                else:
                    print(f"[ERROR] Неизвестная команда 'write {cmd_name}'")

            elif cmd_type == "control":
                if cmd_name in commands.cmd_control_array:
                    controlboard.func_control(cmd_name, ser)
                else:
                    print(f"[ERROR] Неизвестная команда 'control {cmd_name}'")
            
            else:
                print(f"[ERROR] Неизвестный тип команды: '{cmd_type}'. Доступны: read, write, control, help, exit.")

        except Exception as e:
            # Ловим любые ошибки (CRC, таймауты, ошибки парсинга) и продолжаем работать
            print(f"\n[!!!] Произошла ошибка: {e}")
            # Очищаем буфер, если в нем что-то осталось
            if ser.in_waiting > 0:
                ser.reset_input_buffer()
                print("[INFO] Очищен входной буфер порта.")


def main():
    print("--- Интерактивный терминал контроллера ---")
    
    # 1. Запрашиваем порт (используем ваш /dev/ttyUSB2 как порт по умолчанию)
    default_port = "/dev/ttyUSB2"
    port = input(f"Введите COM-порт (по умолч. {default_port}): ")
    if not port:
        port = default_port

    # 2. Запрашиваем скорость
    default_baud = 19200
    try:
        baud = input(f"Введите baudrate (по умолч. {default_baud}): ")
        if not baud:
            baud = default_baud
        else:
            baud = int(baud)
    except ValueError:
        print(f"Неверная скорость, используется {default_baud}.")
        baud = default_baud

    # 3. Открываем порт
    ser = None
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.5  # Таймаут 0.5 сек (важно для REPL)
        )
        print(f"\n[OK] Порт {ser.port} открыт на скорости {ser.baudrate}.")
        
        # 4. Запускаем главный цикл
        main_loop(ser)

    except serial.SerialException as e:
        print(f"\n[FATAL ERROR] Не удалось открыть порт: {e}")
        print("Убедитесь, что службы (edgeserver, vsmd) остановлены и порт указан верно.")
    
    finally:
        if ser and ser.is_open:
            ser.close()
            print(f"\n[OK] Порт {port} закрыт.")

if __name__ == "__main__":
    main()