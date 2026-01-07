# import serial - перенесли для локального использования
import binascii
import argparse
import sys
import os
import time
import struct
import re
import textwrap
import csv

# Добавляем класс для оформления помощи
from argparse import ArgumentDefaultsHelpFormatter, RawTextHelpFormatter

# Импортируем словари с командами
# from commands import ModbusDict, TYPE, DEVICE_ADDR, DEVICE_ADDR_STR, FUNC, REG, Default_Value, cmd_control_array, cmd_read_array, cmd_write_array, cmd_test_array, cmd_util_array
import commands

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
# Таблицы CRC16
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
# конец Таблицы CRC16

ACK = 0x06      # Ответ МК без ошибки
NACK = 0x15     # Ответ МК с ошибкой

func_start = 0    # Точка времени - старт
work_index = 0

class StopRecursion(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

def update_with_serial(file_path, baudrate, serial_port, date_boot: str, ver_f: str, date_f: str, ver_u: str, date_u: str, dev_addr: int):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        func_update(file_path, ser, date_boot, ver_f, date_f, ver_u, date_u, dev_addr)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

def func_update(file_path, ser, date_boot: str, ver_f: str, date_f: str, ver_u: str, date_u: str, dev_addr: int):
    
    print('> !!!NEW!!! UPDATE FUNCTION')
    global func_start
    # Защита от рекурсии
    current_time = int(time.time())
    # print(f'Curren time: {current_time}')
    result_time = current_time - func_start
    print(f'> Result time: {result_time}')
    if result_time > 120:
        raise StopRecursion('Stop recursion.')

    # Проверка указанного формата в пути к файлу
    if not file_path.endswith(".hex"):
        raise Exception(f'Invalid file format: {file_path}. Expected a *.hex file.')
    # Проверка наличия файла по указанному пути
    if not os.path.isfile(file_path):
        raise Exception(f'File not found here: {file_path}')

    print(f"> File {file_path} is valid.")

    # Проверяем, содержит ли файл версию
    if 'Update' in file_path:
        print(f'> We check the file name for the version. Default: {ver_u}')
        match = re.search(r'V\d{2}\.\d{2}\.\d{2}', file_path)
        if match:
            version_str = match.group()[1:]
            ver_u = version_str
            print(f"> Detected version: {ver_u}")
        else: print("> File name don't have a version.")
    else: print("> File name don't have 'Update'.")

    print(f'> Trying send "run" to console by byte (one send, one read etc.)')

    # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
    while ser.in_waiting:
        ser.read(20)

    index = 0
    print(f'> Index start: {index}')

    print(f'> Send byte: {b"r"}')
    ser.write(b"r")
    response = ser.read(1)
    print(f'> Got byte: {response}')
    if response == b"r":
        index += 1
    time.sleep(0.2)

    print(f'> Send byte: {b"u"}')
    ser.write(b"u")
    response = ser.read(1)
    print(f'> Got byte: {response}')
    if response == b"u":
        index += 1
    time.sleep(0.2)

    print(f'> Send byte: {b"n"}')
    ser.write(b"n")
    response = ser.read(1)
    print(f'> Got byte: {response}')
    if response == b"n":
        index += 1
    time.sleep(0.2)

    print(f'> Index finish: {index}')

    # ПРОШИВА или проблемы с передачей данных
    if index == 0:
        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)
        # bytes_version_request_cmd = get_write_cmd(cmd_array["version_request"]["cmd"])      # Получаем команду с CRC16
        
        # hex = binascii.hexlify(bytes_version_request_cmd).decode('utf-8').upper()           # Преобразуем байты в текст для отображения
        # print(f'> Sending bytes: {" ".join(hex[i:i+2] for i in range(0, len(hex), 2))}')      # Заделяем пробелами, отправляем в консоль
        
        # ser.write(bytes_version_request_cmd)                                                # Отправляем байты-команду микроконтроллеру
        # response = ser.read(10)                                                             # Читаем 10 байт
        
        # res_hex = binascii.hexlify(response).decode('utf-8').upper()                        # Получаем строку байт для отображения
        # print(f'> Received: {" ".join(res_hex[i:i+2] for i in range(0, len(res_hex), 2))}')   # Разделяем байты пробелами и в консоль

        response = send_and_get(commands.cmd_read_array['version_request'], 7, ser, ov_addr=dev_addr)
        
        if len(response) == 0:
            raise Exception('Device not responding!!!')
        
        string_ver = b'\x04\x02\x20\x00'    # было b'\x04\x02\x14\x00'

        if string_ver in response:
            ''' Сбрасываем МК '''
            cmd_info = commands.cmd_control_array['reset']   # получаем все данные о команде (чтобы получить массив данных только этой команды, а не всей табляцы cmd_array_new)
            send_cmd = build_modbus_cmd(cmd_info["modbus"],override_address=dev_addr)
            response = send_and_get(cmd_info, 8, ser, ov_addr=dev_addr)
                
            # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
            while ser.in_waiting:
                ser.read(20)

            if send_cmd not in response:
                raise Exception(f'Except bytes "{send_cmd}" in the response: {response}')

            time.sleep(3)   # Заснем на 3 сек. для ожидания перезагрузки МК и прыжка

            func_update(file_path, ser, date_boot, ver_f, date_f, ver_u, date_u, dev_addr) 
        else:
            raise Exception(f'Except the order of bytes "{string_ver}" in the response: {response}')
    # КОНСОЛЬ
    elif index == 3:
        ser.write(b'\n')
        response = ser.read(100)    # Читаем текст отправляемый МК-м

        if b"[MENU]:" in response:
            print('> Response to console: [MENU]:...\r\n>>> Update mode <<<')
            
            # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
            while ser.in_waiting:
                ser.read(20)

            send_to_console(b'run', ser)
            response = ser.read(100)

        if not b'Information about board:' in response:
            raise Exception(f"Unexpected response: {response.decode('utf-8')}")
        else:
            print("> Sent 'run' to console.")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        send_to_console(b'yes', ser)        # МК присылает тех. информацию, а потом спрашивает записали ли мы заводскую прошивку, отвечаем 'yes'
        response = ser.read(100)
        print("> Sent 'yes' to console.")   # Предыдущая команда прошла

        if len(response) == 0:
            raise Exception('Device not responding!!!')
        
        if b'At first look you lied!!!' in response:
            # ---------------------[!!!!!] Но тут мы можем реализовать загрузку заводской прошивки [!!!!!]----------------------
            raise Exception("You didn't upload the Factory Firmware! We are in the updating mode. Please, upload the factory firmware and repeat.")

        if b'Failed: erase update.' in response:
            raise Exception('Flash memory space for update is not erased.')

        # ПЕРВЫЙ СТАРТ
        if b'Set the date of uploading Bootloader' in response:

            # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
            while ser.in_waiting:
                ser.read(20)
            
            send_to_console(date_boot.encode('utf-8'), ser)
            print(f'> Current data: {date_boot}')
            response = ser.read(100)

            # Такой текст выплевываеи МК для продолжения процесса
            if b'Set the version of the Factory Firmware' in response:
                print("> Bootloader firmware date entered.")                  # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                send_to_console(ver_f.encode('utf-8'), ser)
                print(f'> Current version: {ver_f}')
                response = ser.read(100)
            else:
                raise Exception(f"Unexpected response: {response.decode('utf-8')}")
            
            # Такой текст выплевываеи МК для продолжения процесса
            if b'Set the date of uploading Factory Firmware' in response:
                print("> Factory firmware version entered.")                  # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                send_to_console(date_f.encode('utf-8'), ser)
                print(f'> Current data: {date_f}')
                response = ser.read(100)
            else:
                raise Exception(f"Unexpected response: {response.decode('utf-8')}")
            
            # Такой текст выплевываеи МК для продолжения процесса
            if b"Let's jump to the Factory Firmware?" in response:
                print("> Factory firmware date entered.")                  # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                print('> Send "yes"')
                send_to_console(b'yes', ser)
                response = ser.read(100)
                
                if b'Faild Flash Tech Page!!!' in response:
                    raise Exception('Failed Flash Tech Page!!!')
                
                # print('> Resetting... Please, wait about 40 sec!!!')

                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                for i in range(20, -1, -1):  # от 20 до 0
                    print(f'\r\033[33m> Resetting... Please, wait about {i} sec!!!\033[0m', end='', flush=True)
                    time.sleep(1)

                func_update(file_path, ser, date_boot, ver_f, date_f, ver_u, date_u, dev_addr)    # перезапуск апдейта в результате ветки первого старта

        # UPDATE
        elif b'Erasing the update memory' in response:
            # Получаем кол-во строк для отображения загрузку в процентах
            with open(file_path, 'r') as file:
                total_lines = sum(1 for _ in file)
            
            # Чтение файла построчно
            with open(file_path, 'r') as file:
                # Читаем две первые строчки hex-файла для проверки адреса прошивки:
                # у обычной прошивки 0x08000000 (без бутлоадера),
                # у заводской прошивки 0x0800C000 (с предварительно зашитым бутлоадером),
                # у апдейта прошивки 0x08040000 (с предварительно зашитым бутлоадером),
                line1 = file.readline()
                line2 = file.readline()

                # Строки hex должны начинаться с ':'
                if line1[0] != ':' or line2[0] != ':':
                    raise Exception(f'Failed structure of file. In *.hex string starts from ":"')

                # Берем необходимые данный, проверив формат
                if line1[1:3] == "02" and line1[7:9] == "04":
                    high_bytes_addr = line1[9:13]
                if line2[7:9] == "00":
                    low_bytes_addr = line2[3:7]

                # Проверяем соответствие адресу апдейта
                if high_bytes_addr != "0804" and low_bytes_addr != "0000":
                    raise Exception(f'Failed address for update: 0x{high_bytes_addr}{low_bytes_addr}')

                file.seek(0)    # Сбрасываем указатель на начало файла

                print(f'> Start address for update: 0x{high_bytes_addr}{low_bytes_addr}')

                # Тут начинается непостредственно процесс передачи прошивки
                print("> Erasing the update memory...")
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                count = 0
                time.sleep(3.0)
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                for line in file:
                    ser.write(line.encode('utf-8'))
                    response = ser.read(1)
                    if len(response) == 0:
                        raise Exception("Don't have response after sending line.")
                    if response[0] == NACK:
                        response = ser.read(100)
                        raise Exception(f"Some error during the process. Text from MCU:\r\n{response.decode('utf-8')}")
                    if response[0] == ACK:
                        count += 1
                        percent = int((count / total_lines) * 100)
                        print(f'\r\033[33m> Flash memory writing progress: [{percent}%]\033[0m', end='', flush=True)
     
            response = ser.read(100)

            print('\r\n') 

            if b'The process was successful' in response:
                print("\033[32m>>> The process was successful! <<<\033[0m\r\n")                           # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                send_to_console(ver_u.encode('utf-8'), ser)
                print(f'> Current version: {ver_u}')
                response = ser.read(100)
            else:
                raise Exception(f"Message: {response.decode('utf-8')}")

            if b'Set the date of the updating' in response:
                print("> Update firmware version entered.")                           # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                send_to_console(date_u.encode('utf-8'), ser)
                print(f'> Current date: {date_u}')
                response = ser.read(100)
                print(f'> Response: "{response.decode("utf-8")}"')
            else:
                raise Exception(f"Unexpected response: {response.decode('utf-8')}")

            if b"Let's jump to the Updated Firmware" in response:
                print("> Update firmware date entered.")                           # Предыдущая команда прошла
                
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                print('> Send "yes"')
                send_to_console(b'yes', ser)
                response = ser.read(100)
                print(f'> Response: "{response.decode("utf-8")}" \r\n> WAIT...')
                time.sleep(3.0)
                print('>>> Finished!!! <<<')
            else:
                raise Exception(f"Unexpected response: {response.decode('utf-8')}")

            if b'Faild Flash Tech Page' in response:
                raise Exception('Some problem with a writing flash page.')
        else:
            raise Exception(f"Unexpected response: {response.decode('utf-8')}")

def get_write_cmd(cmd: str):
    bytes_command = binascii.unhexlify(cmd.replace(' ', ''))    # Преобразуем строчку в байты
    crc = crc16(bytes_command).to_bytes(2, byteorder='big')     # Рассчитываем CRC16 и переводим в 2 байта
    bytes_command += crc                                        # Прибавояем к команде из байт 2 бата CRC16
    return bytes_command

""" Проверка CRC16 """
def valid_crc16(response: bytes) -> bool:
    response_crc = int.from_bytes(response[-2:], byteorder='big')
    # print(f'> Received CRC16: {response_crc}')
    crc = crc16(response[:-2])
    # print(f'> Calculated CRC16: {response_crc}')
    if response_crc == crc:
        return True
    return False

""" Отправка строки в консоль
У нас после каждого отправленного байта в консоль возвращается он же обратно
для отображения символа в консоли. Соответственно мы должны отправлять байт
строки, получать его же обратно. Таким способом будет передаваться строка."""
def send_to_console(str_bytes: bytes, ser):
    for byte in str_bytes:
        # print(f'Byte: {bytes([byte])}')
        ser.write(bytes([byte]))
        response = ser.read(1)
        # print(f'Got: {response}')
        time.sleep(0.2)
        if not response:
            raise Exception(f'No response for byte: {byte}')
        if byte != response[0]:
            raise Exception(f'Not the same byte: {byte} != {response[0]}')
    ser.write(b'\n')

def control_with_serial(baudrate, serial_port, cmd: str):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        func_control(cmd, ser)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

# Функция управления платой (например, вкл./выкл., сросить)
def func_control(cmd: str, ser):
    '''
    Данная функция используется для отправки команд как они есть
    '''
    cmd_array = commands.cmd_control_array[cmd]
    cmd_modbus  = cmd_array["modbus"]

    address     = cmd_modbus["address"]
    function    = cmd_modbus["function"]
    register    = cmd_modbus["register"]
    value       = cmd_modbus["value"]

    # Собираем команду (без CRC)
    raw_cmd = (
        address.to_bytes(1,"big") +
        function.to_bytes(1,"big") +
        register.to_bytes(2,"big") +
        value.to_bytes(2,"big")
    )

    # Дополнительно можно проверить, что первые 6 байт совпадают
    # (адрес, функция, регистр, значение) — здесь send_cmd[:6]
    # Часто контроллер возвращает тот же набор, если команда принята.
    response = send_and_get(cmd_array, 8, ser)
    if raw_cmd not in response:
        raise Exception(f'Some issues with control!!! Compare send bytes and received')
    else:
        text_result = "========================================\n"
        text_result += f'          >>> Well done!!! <<<\n'
        text_result += "========================================"
        print(f'{text_result}')
    #pass # Заглушка

def read_with_serial(baudrate, serial_port, cmd: str):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        func_read(cmd, ser)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

# Функция чтения данных с датчиков и переменных прошивки
def func_read(cmd: str, ser):
    cmd_array = commands.cmd_read_array[cmd]   # сохраняем данные команды
      
    match cmd:
        case "version_request":
            response = send_and_get(cmd_array, 7, ser)
            if b'\x04\x02\x20\x00' not in response: # было b'\x04\x02\x14\x00'
                raise Exception(f'Incorrect version!!!')
            else:
                text_result = "========================================\n"
                text_result += f'       >>> Version is right!!! <<<\n'
                text_result += "========================================"
                print(f'{text_result}')
        case "coils":
            response_1 = send_and_get(cmd_array, 6, ser, ov_reg=commands.REG.REG_VSM_PC_PWR, ov_value=8)
            response_2 = send_and_get(cmd_array, 6, ser, ov_reg=commands.REG.REG_RADAR_PWR,  ov_value=8)
            
            # Разбираем посылку
            bytes_1 = int(response_1[2])    # Кол-во байт данных
            data_1  = response_1[3:-2]      # Сами данные

            bytes_2 = int(response_2[2])    # Кол-во байт данных
            data_2  = response_2[3:-2]      # Сами данные
            
            # Проверка длинны
            if bytes_1 != len(data_1):
                raise Exception(f"Number of bytes error: Expected {bytes_1}, but got {len(data_1)}.")
            if bytes_2 != len(data_2):
                raise Exception(f"Number of bytes error: Expected {bytes_2}, but got {len(data_2)}.")

            # Расшифровка битов состояния
            data_flags = {
                "PC Power"          : (data_1[0] >> 0) & 1,
                "Heater_1 Power"    : (data_1[0] >> 1) & 1,
                "Heater_2 Power"    : (data_1[0] >> 2) & 1,
                "PC SW"             : (data_1[0] >> 5) & 1,
                "Frozen Request"    : (data_1[0] >> 7) & 1,
                "Radar Power"       : (data_2[0] >> 0) & 1,
                "Camera Power"      : (data_2[0] >> 1) & 1,
                "GPS Power"         : (data_2[0] >> 2) & 1,
                "Heater_1 Power"    : (data_2[0] >> 3) & 1,
            }

            print("Decoded Coil Flags:")
            for name, state in data_flags.items():
                print(f"-----> {name}: {'ON' if state else 'OFF'}")
        case "states":
            response = send_and_get(cmd_array, 6, ser, ov_reg=commands.REG.AC_OK, ov_value=8)

            # Разбираем посылку
            bytes_count = int(response[2])    # Кол-во байт данных
            data        = response[3:-2]      # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")

            # Расшифровка битов состояния
            data_flags = {
                "AC_OK"         : (data[0] >> 0) & 1,
                "Battery Low"   : (data[0] >> 1) & 1,
                "5V from PC"    : (data[0] >> 2) & 1,
                "FAN Blocked"   : (data[0] >> 4) & 1,
                "Frozen Mode"   : (data[0] >> 5) & 1,
            }

            print("Decoded Coil Flags:")
            for name, state in data_flags.items():
                print(f"-----> {name}: {'ON' if state else 'OFF'}")
        case "temp":
            response = send_and_get(cmd_array, 8, ser)

            data    = response[4:-2]     # Сами данные
            
            # Проверка длинны
            if len(data) != 2:
                raise Exception(f"Number of bytes error: Expected 2, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]

            # Если отрицательное значение
            if result & 0x8000:
                result -= 0x10000

            text_result = "========================================\n"
            text_result += f'  >>> Temperature: {result} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "pc_wdt":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Seconds left: {result} [s] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "voltage":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Input voltage: {result} [mV] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "temperature":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            result /= 2
            text_result = "========================================\n"
            text_result += f'  >>> Temperature: {result:.1f} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "current":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            result *= 10
            text_result = "========================================\n"
            text_result += f'  >>> Input current: {result} [mA] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "start_temp":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result_lo = (data[0] << 8) | data[1]
            if result_lo & 0x8000:
                result_lo -= 0x10000
            result_hi = (data[2] << 8) | data[3]
            text_result = "========================================\n"
            text_result += f'  >>> Start tempetarue (config): {result_lo}...{result_hi} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "work_temp":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result_lo = (data[0] << 8) | data[1]
            if result_lo & 0x8000:
                result_lo -= 0x10000
            result_hi = (data[2] << 8) | data[3]
            text_result = "========================================\n"
            text_result += f'  >>> Work tempetarue (config): {result_lo}...{result_hi} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "pre_temp":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Preheating temperature (config): {result} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "hyst":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Hysteresis (config): {result} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "voltage_limits":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result_hi = (data[0] << 8) | data[1]
            result_lo = (data[2] << 8) | data[3]
            text_result = "========================================\n"
            text_result += f'  >>> Voltage limits (config): {result_lo}...{result_hi} [mV] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "current_limits":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result_lo = (data[0] << 8) | data[1]
            result_hi = (data[2] << 8) | data[3]
            text_result = "========================================\n"
            text_result += f'  >>> Current limits (config): {result_lo}...{result_hi} [mA] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "firmware_version":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            text_result += f'  >>> Firmware version: V{data[0]:02X}.{data[1]:02X} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "heat_temp":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            heater1 = (data[0] << 8) | data[1]
            heater2 = (data[2] << 8) | data[3]
            text_result = "========================================\n"
            text_result += f'  >>> Temperature for heaters (config): HEATER1 - {heater1} [॰С], HEATER2 - {heater2} [॰С] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "serial_number":
            response = send_and_get(cmd_array, 17, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            serial = ''.join(f'{b:02X}' for b in data)
            text_result += f'  >>> MCU serial number: {serial} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "with_fan":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> With FAN? (config): {"YES" if result else "NO"} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "ups_conf":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> UPS (config): {result} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "bat_low_limit":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Battery low less then: {result} [mV] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "timer":
            response = send_and_get(cmd_array, 11, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[2] << 24) | (data[3] << 16) | (data[0] << 8) | data[1]
            rollover = (data[4] << 8) | data[5]
            result = 0xFFFFFFFF * rollover + result # Сырые данные в секундах

            h = result // 3600
            m = (result % 3600) // 60
            s = result % 60
            
            text_result = "========================================\n"
            text_result += f'  >>> Worked time: {h}:{m:02}:{s:02} ({result} [s] - {result//60} [min]) <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "accum":
            accum = send_and_get(cmd_array, 13, ser)
            timer = send_and_get(commands.cmd_read_array['timer'], 11, ser)
    
            # Разбираем посылку
            accum_bytes = int(accum[2])     # Кол-во байт
            accum_data  = accum[3:-2]       # Сами данные
            timer_bytes = int(timer[2])     # Кол-во байт
            timer_data  = timer[3:-2]       # Сами данные
            
            # Проверка длинны
            if accum_bytes != len(accum_data):
                raise Exception(f"Number of bytes error: Expected {accum_bytes}, but got {len(accum_data)}.")
            if timer_bytes != len(timer_data):
                raise Exception(f"Number of bytes error: Expected {timer_bytes}, but got {len(timer_data)}.")
            
            # Парсим данные потребления
            if len(accum_data) != 8:
                raise ValueError("Expected exactly 6 bytes")

            print(f'data[0]: {accum_data[0]} data[1]: {accum_data[1]} data[2]: {accum_data[2]} data[3]: {accum_data[3]} data[4]: {accum_data[4]} data[5]: {accum_data[5]} data[6]: {accum_data[6]} data[7]: {accum_data[7]}')
            # Little-endian (Modbus: LSB first)
            ACCUM_lo = (accum_data[0] << 8) | accum_data[1]       # REG_GET_ACCUM_W_LO
            print(f'REG_GET_ACCUM_W_LO: {ACCUM_lo}')
            ACCUM_hi = (accum_data[2] << 8) | accum_data[3]       # REG_GET_ACCUM_W_HI
            print(f'REG_GET_ACCUM_W_HI: {ACCUM_hi}')

            AVG_P_lo = (accum_data[4] << 8) | accum_data[5]       # REG_GET_AVG_P_LO
            print(f'REG_GET_AVG_P_LO: {ACCUM_lo}')
            AVG_P_hi = (accum_data[6] << 8) | accum_data[7]       # REG_GET_AVG_P_HI
            print(f'REG_GET_AVG_P_LO: {ACCUM_lo}')


            # Собираем 32-битное значение ватт
            pre_Wh = (ACCUM_hi << 16) | ACCUM_lo
            print(f'pre_Wh: {pre_Wh}')
            Wh = pre_Wh / 1000.0
            print(f'Wh: {Wh}')
            
            pre_avg_power = (AVG_P_hi << 16) | AVG_P_lo
            print(f'pre_avg_power: {pre_avg_power}')
            avg_power = pre_avg_power / 1000.0
            print(f'avg_power: {avg_power}')

            timer_result = (timer_data[2] << 24) | (timer_data[3] << 16) | (timer_data[0] << 8) | timer_data[1]
            timer_rollover = (timer_data[4] << 8) | timer_data[5]
            timer_result = 0xFFFFFFFF * timer_rollover + timer_result

            h = timer_result // 3600
            m = (timer_result % 3600) // 60
            s = timer_result % 60

            text_result = "========================================\n"
            text_result += f'  >>> Accumulated: {Wh:.3f} [Wh] in {h}:{m:02}:{s:02} <<<\n'
            text_result += f'  >>> Average consumption: {avg_power} [Wh] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "humidity":
            response = send_and_get(cmd_array, 7, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result = (data[0] << 8) | data[1]
            text_result = "========================================\n"
            text_result += f'  >>> Humidity: {result} [%] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "pressure":
            response = send_and_get(cmd_array, 9, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            result_lo = (data[0] << 8) | data[1]
            result_hi = (data[2] << 8) | data[3]
            result = (result_hi << 16) | result_lo
            text_result = "========================================\n"
            text_result += f'  >>> Pressure: {result/100:.2f} [mbar] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        case "tech_data":
            response = send_and_get(cmd_array, 27, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            # здесь должна быть расшифровка данных
            match(data[0]):
                case 0xFF:
                    execution = "Base without Bootloader"
                case 0x00:
                    execution = "Factory"
                case 0x01:
                    execution = "Update"
                case _:
                    execution = "-"
            text_result += f'  >>> Active Firmware: {execution}\n'
            text_result += f'  >>> Bootloader Version: {data[1] if data[1] != 0xFF else "-"}.{data[2] if data[2] != 0xFF else "-"}.{data[3] if data[3] != 0xFF else "-"}\n'
            text_result += f'  >>> Bootloader Date of uploading: '  # Даты у нас хранятся как есть, например: 0x10 - это десятое число, 0x06 - месяц, 0x25 - год
            text_result += f'{((data[4] >> 4) * 10) + (data[4] & 0x0F) if data[4] != 0xFF else "-"}'
            text_result += f'.{((data[5] >> 4) * 10) + (data[5] & 0x0F) if data[5] != 0xFF else "-"}'
            text_result += f'.20{((data[6] >> 4) * 10) + (data[6] & 0x0F) if data[6] != 0xFF else "-"}\n'
            text_result += f'  >>> Factory Version: {data[7] if data[7] != 0xFF else "-"}.{data[8] if data[8] != 0xFF else "-"}.{data[9] if data[9] != 0xFF else "-"}\n'
            text_result += f'  >>> Factory Date of uploading: '
            text_result += f'{((data[10] >> 4) * 10) + (data[10] & 0x0F) if data[10] != 0xFF else "-"}'
            text_result += f'.{((data[11] >> 4) * 10) + (data[11] & 0x0F) if data[11] != 0xFF else "-"}'
            text_result += f'.20{((data[12] >> 4) * 10) + (data[12] & 0x0F) if data[12] != 0xFF else "-"}\n'
            text_result += f'  >>> Update Version: {data[13] if data[13] != 0xFF else "-"}.{data[14] if data[14] != 0xFF else "-"}.{data[15] if data[15] != 0xFF else "-"}\n'
            text_result += f'  >>> Update Date of uploading: '
            text_result += f'{((data[16] >> 4) * 10) + (data[16] & 0x0F) if data[16] != 0xFF else "-"}'
            text_result += f'.{((data[17] >> 4) * 10) + (data[17] & 0x0F) if data[17] != 0xFF else "-"}'
            text_result += f'.20{((data[18] >> 4) * 10) + (data[18] & 0x0F) if data[18] != 0xFF else "-"}\n'
            
            match(data[19]):
                case 0:
                    ver_status = "Undefined"    # если функция не отработала
                case 1:
                    ver_status = "Was right version" #
                case 2:
                    ver_status = "Firmware without Bootloader"
                case 3:
                    ver_status = "Some problem with variable FIRMWARE_VERSION_STR"
                case 4:
                    ver_status = "Correct version loaded into flash"
                case 5:
                    ver_status = "Flash ERROR"
                case _:
                    ver_status = "-"
            text_result += f'  >>> Status of the last firmware version check (Active Firmware): {ver_status}\n'

            reg_count = (data[20] << 8) | data[21]
            # print(f'count: {reg_count}')
            text_result += f'  >>> Сount of the registers firmware project name: {reg_count} (bytes: {reg_count * 2})\n'
            project_response = send_and_get(commands.cmd_read_array['project_name'], (5 + reg_count * 2), ser, ov_value=reg_count)

            # Разбираем посылку
            prj_bytes_count = int(project_response[2])  # Кол-во байт
            prj_data        = project_response[3:-2]            # Сами данные
            
            # Проверка длинны
            if prj_bytes_count != len(prj_data):
                raise Exception(f"Number of bytes error: Expected {prj_bytes_count}, but got {len(prj_data)}.")
            
            text_result += f'  >>> Project: {prj_data.decode("utf-8")}\n'
            text_result += "========================================"
            print(f'{text_result}')

        case "imu":
            response    = send_and_get(cmd_array, 29, ser)
            bytes_count = int(response[2])      # Кол-во байт
            imu_data    = response[3:-2]        # Сами данные

            if bytes_count != len(imu_data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(imu_data)}.")
            
            status  = (imu_data[0] << 8) | imu_data[1]
            gravity = (imu_data[2] << 8) | imu_data[3]
            a_scale = (imu_data[4] << 8) | imu_data[5]
            g_scale = (imu_data[6] << 8) | imu_data[7]
            accel_x = (imu_data[8] << 8) | imu_data[9]
            accel_y = (imu_data[10] << 8) | imu_data[11]
            accel_z = (imu_data[12] << 8) | imu_data[13]
            gyro_x  = (imu_data[14] << 8) | imu_data[15]
            gyro_y  = (imu_data[16] << 8) | imu_data[17]
            gyro_z  = (imu_data[18] << 8) | imu_data[19]
            pitch   = (imu_data[20] << 8) | imu_data[21]
            roll    = (imu_data[22] << 8) | imu_data[23]

            # проверяем на отрицательность значения
            if accel_x & 0x8000:    accel_x -= 0x10000
            if accel_y & 0x8000:    accel_y -= 0x10000
            if accel_z & 0x8000:    accel_z -= 0x10000
            if gyro_x & 0x8000:     gyro_x -= 0x10000
            if gyro_y & 0x8000:     gyro_y -= 0x10000
            if gyro_z & 0x8000:     gyro_z -= 0x10000
            if pitch & 0x8000:      pitch -= 0x10000
            if roll & 0x8000:       roll -= 0x10000

            match status:
                case 0:
                    text_status = 'ICM_FIRST_START'
                case 1:
                    text_status = 'ICM_OK'
                case 2:
                    text_status = 'ICM_ERR_NOT_RESP'
                case 3:
                    text_status = 'ICM_ERR_WHO_AM_I'
                case 4:
                    text_status = 'ICM_ERR_RESET'
                case 5:
                    text_status = 'ICM_ERR_CLK'
                case 6:
                    text_status = 'ICM_ERR_SLEEP_MODE'
                case 7:
                    text_status = 'ICM_ERR_INTERFACE'
                case 8:
                    text_status = 'ICM_ERR_TO_BANK2'
                case 9:
                    text_status = 'ICM_ERR_GYRO_DIV'
                case 10:
                    text_status = 'ICM_ERR_GYRO_CFG1'
                case 11:
                    text_status = 'ICM_ERR_GYRO_CFG2'
                case 12:
                    text_status = 'ICM_ERR_ACCEL_DIV'
                case 13:
                    text_status = 'ICM_ERR_ACCEL_CFG1'
                case 14:
                    text_status = 'ICM_ERR_ACCEL_CFG2'
                case 15:
                    text_status = 'ICM_ERR_TO_BANK0'
                case 16:
                    text_status = 'ICM_ERR_ACCEL_GYRO_ON'
                case 17:
                    text_status = 'ICM_BUSY'
                case _:
                    text_status = 'unknown'

            text_result = "========================================\n"
            text_result += f'Status ICM-20948 Initialization: {text_status}\n'
            text_result += f'Gravitational Acceleration: {(gravity/1000):.3f} [m/c2]\n'
            text_result += f"Accelerometer Scale: a_scale={a_scale} (g*a_scale in MCU)\n"
            text_result += f'Gyroscope Scale: g_scale={g_scale} (dps*g_scale in MCU)\n'
            text_result += "========================================\n"
            text_result += f"[A_X: {accel_x}] [A_Y: {accel_y}] [A_Z: {accel_z}] [G_X: {gyro_x}] [G_Y: {gyro_y}] [G_Z: {gyro_z}] [PITCH: {pitch}] [ROLL: {roll}]\n"
            text_result += "========================================"
            print(f'{text_result}')

        case "rtc":
            response = send_and_get(cmd_array, 11, ser)
    
            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            text_result += f'  >>> Date: {data[2]:02}.{data[1]:02}.20{data[0]:02} <<<\n'
            text_result += f'  >>> Time: {data[3]:02}:{data[4]:02}:{data[5]:02} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')

        case "frame_mult":
            response = send_and_get(cmd_array, 17, ser)

            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            text_result += f'  >>> Frame Multiplication of the Inner Channel: X{data[1]} <<<\n'
            text_result += f'  >>> Frame Multiplication of the External Channel: X{data[11]} <<<\n'
            text_result += "========================================"
            print(f'{text_result}')

        case "frame_state":
            response = send_and_get(cmd_array, 23, ser)

            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные

            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            text_result += f'  >>> Frame Multiplication of the Inner Channel: X{data[1]} <<<\n'

            if data[1] > 1:
                text_result += '  >>> Frame Works: '
                match data[7]:
                    case 0:
                        text_result += 'No One <<<\n'
                    case 1:
                        text_result += 'Inner <<<\n'
                    case 2:
                        text_result += 'External <<<\n'
                    case _:
                        text_result += '- <<<\n'

                text_result += '  >>> Frame Step: '
                match data[5]:
                    case 0:
                        text_result += 'waiting rising <<<\n'
                    case 1:
                        text_result += 'waiting falling <<<\n'
                    case 2:
                        text_result += 'waiting second rising to get period <<<\n'
                    case 3:
                        text_result += 'got the risings, fallings and periods <<<\n'
                    case 4:
                        text_result += 'frames ready for a generation<<<\n'
                    case 5:
                        text_result += 're-check pulse width <<<\n'
                    case 6:
                        text_result += "after generation check that don't loose input frames (??? hope we don't need it) <<<\n"
                    case _:
                        text_result += '- <<<\n'

                text_result += f'  >>> Frame Flags: 0x{data[3]:02X}\n'
                if data[3] & 0x01: text_result += '          IC EXTERNAL\n'
                if data[3] & 0x02: text_result += '          IC INNER\n'
                if data[3] & 0x08: text_result += '          calculated\n'
                if data[3] & 0x10: text_result += '          OUT EXTERNAL\n'
                if data[3] & 0x20: text_result += '          OUT EXTERNAL\n'
                if data[3] & 0x40: text_result += '          start waiting stop PWM\n'
                if data[3] & 0x80: text_result += '          start waiting frame loss\n'
            else:
                text_result += '  >>> Full statistic works only with multiplication X2 or more <<<\n'
            text_result += "========================================"

            text_result += f'  >>> Frame Multiplication of the Inner Channel: X{data[11]} <<<\n'

            if data[11] > 1:
                text_result += '  >>> Frame Works: '
                match data[17]:
                    case 0:
                        text_result += 'No One <<<\n'
                    case 1:
                        text_result += 'Inner <<<\n'
                    case 2:
                        text_result += 'External <<<\n'
                    case _:
                        text_result += '- <<<\n'

                text_result += '  >>> Frame Step: '
                match data[15]:
                    case 0:
                        text_result += 'waiting rising <<<\n'
                    case 1:
                        text_result += 'waiting falling <<<\n'
                    case 2:
                        text_result += 'waiting second rising to get period <<<\n'
                    case 3:
                        text_result += 'got the risings, fallings and periods <<<\n'
                    case 4:
                        text_result += 'frames ready for a generation<<<\n'
                    case 5:
                        text_result += 're-check pulse width <<<\n'
                    case 6:
                        text_result += "after generation check that don't loose input frames (??? hope we don't need it) <<<\n"
                    case _:
                        text_result += '- <<<\n'

                text_result += f'  >>> Frame Flags: 0x{data[13]:02X}\n'
                if data[13] & 0x01: text_result += '          IC EXTERNAL\n'
                if data[13] & 0x02: text_result += '          IC INNER\n'
                if data[13] & 0x08: text_result += '          calculated\n'
                if data[13] & 0x10: text_result += '          OUT EXTERNAL\n'
                if data[13] & 0x20: text_result += '          OUT EXTERNAL\n'
                if data[13] & 0x40: text_result += '          start waiting stop PWM\n'
                if data[13] & 0x80: text_result += '          start waiting frame loss\n'
            else:
                text_result += '  >>> Full statistic works only with multiplication X2 or more <<<\n'
            text_result += "========================================"

            print(f'{text_result}')
        case "autoheat_mode":
            response = send_and_get(cmd_array, 7, ser)

            # Разбираем посылку
            bytes_count = int(response[2])      # Кол-во байт
            data        = response[3:-2]        # Сами данные
            
            # Проверка длинны
            if bytes_count != len(data):
                raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(data)}.")
            
            text_result = "========================================\n"
            text_result += '  >>> Auto Heat Mode: '
            match data[1]:
                case 0:
                    text_result += 'both work in ON-OFF mode <<<\n'
                case 1:
                    text_result += 'heater 1 in PWM mode but heater 2 in ON-OFF <<<\n'
                case 2:
                    text_result += 'heater 1 in ON-OFF but heater 2 in PWM mode <<<\n'
                case 3:
                    text_result += 'both work in PWM mode <<<\n'
                case 4:
                    text_result += 'only heater 1 in ON-OFF mode, heater 2 in manual mode <<<\n'
                case 5:
                    text_result += 'only heater 2 in ON-OFF mode, heater 1 in manual mode <<<\n'
                case 6:
                    text_result += 'only heater 1 in PWM mode, heater 2 in manual mode <<<\n'
                case 7:
                    text_result += 'only heater 2 in PWM mode, heater 1 in manual mode <<<\n'
                case _:
                    text_result += '- <<<\n'
            text_result += "========================================"
            print(f'{text_result}')

        case _:
            response = send_and_get(cmd_array, 10, ser)

            if response[1] == 0x4 and response[2] in (0x80, 0x82, 0x86, 0x8A):
                if not len(response) == 10:
                    raise Exception(f'Bytes: {len(response)} (should be 10)')
                buffer = [response[4], response[5], response[6], response[7]]

                match response[3]:
                    case 0x88:
                        text = 'Voltage'
                        unit = 'V'
                    case 0x57:
                        text = 'Over Voltage Limit'
                        unit = 'V'
                    case 0x58:
                        text = 'Under Voltage Limit'
                        unit = 'V'
                    case 0x86:
                        text = 'Сonsumption Since Switching On'
                        unit = 'kW'
                    case 0xD1:
                        text = 'Voltage Drop Across the Input Shunt'
                        unit = 'V'
                    case 0x89:
                        text = 'Current'
                        unit = 'A'
                    case 0x4A:
                        text = 'Current Limit'
                        unit = 'A'
                    case 0x97:
                        text = 'Power'
                        unit = 'W'
                    case 0x6B:
                        text = 'Power Limit'
                        unit = 'W'
                # Преобразуем массив в float
                print(f"{text} = {struct.unpack('f', bytes(buffer))[0]} {unit}")
            else:
                print(f"Unknown command")

def write_with_serial(baudrate, serial_port, cmd: str, value: str | None = None):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        func_write(cmd, ser, value)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

# Функция управления со значением (например, шагов)
def func_write(cmd: str, ser, value: str | None = None):
    '''
    Данная функция используется для отправки команд со значением от которого зависит 
    '''
    cmd_array   = commands.cmd_write_array[cmd]    # сохраняем данные команды
    send_cmd    = []                    # массив для многосоставных команд, таких как фокус и зум

    if cmd in ["heat1_on","heat2_on","heat1_off","heat2_off","focus","zoom","diaph","cam_filter"]:
        if cmd in ["heat1_on","heat2_on"]:
            if value is None:
                result_val = 0x00
            else:
                try:
                    result_val = int(value)
                except ValueError:
                    raise Exception('Set the number!')
                if result_val < 1 or result_val > 0xFF:
                    raise Exception('Number should be > 0 <= 255.')
            result_val = (0xFF << 8) | result_val
            temp_cmd = build_modbus_cmd(cmd_array["modbus"], override_value=result_val)
            send_cmd.append(temp_cmd)
        elif cmd in ["heat1_off","heat2_off"]:
            func_control(cmd, ser)
            return
        elif cmd in ["focus","zoom","diaph","cam_filter"]:
            if value and '>' in value:
                side = 0        # по часовой
            elif value and '<' in value:
                side = 1        # против часовой
            else:
                raise Exception('Set direction: < (anticlockwise) or > (clockwise)')
            
            # Отделяем число от команды
            m = re.search(r'\d+', value)                            # ищем число по регулярному выражению
            if not m:                                               # если не нашел
                raise Exception(f"Not found number.")               # выдаем эксепшен
            try:
                number = int(m.group())                             # пробуем парсить до целого
            except ValueError:                                      # если не получилось
                raise Exception('Some issues with the number!!!')  # выдаем эксепшен
            
            result_val  = 0x0   # переменная в которой мы формируем значение
            start_power = 0x0F  # начальная самая большая степень, чтобы начать с очень большого числа

            # Цикл разбора большого числа на команды
            if number > 0xFF:
                while start_power >= 0x08:                  # если степень >= 8, так реализовано в МК - степень в диапазоно 8...15 (0x8...0xF)
                    while number >= 2**start_power:          # если значение >= чем 2^(степень 8...15)
                        number = number - 2**start_power                                            # вычитаем большую часть
                        result_val = (0x8 << 12) | (side << 8) | (start_power & 0xFF)               # заносим в результат: [старший бит - степенная команда (0x8000)] - [в какую сторону] - []
                        temp_cmd = build_modbus_cmd(cmd_array["modbus"], override_value=result_val)  # формируем команду
                        send_cmd.append(temp_cmd)                                                   # добавляем в массив команд
                        result_val = 0x0                                                            # обнуляем результа, на всякий
                    start_power -= 1                        # понижаем степень

            # Обработка остатка или формирование команды с малым значениес (1 байт)
            if number > 0 and number <= 0xFF:                                               # если осталось малое число 1...255             
                result_val = (side << 8) | (number & 0xFF)
                number -= number   # обнуляем остаток
                temp_cmd = build_modbus_cmd(cmd_array["modbus"], override_value=result_val)
                send_cmd.append(temp_cmd)
            
            if number != 0:
                raise Exception(f'Some remainder: {number}')
        # elif cmd == "diaph":
        #     if value and '>' in value:
        #         side = 0        # по часовой
        #     elif value and '<' in value:
        #         side = 1        # против часовой
        #     else:
        #         raise Exception('Set direction: < (anticlockwise) or > (clockwise)')
            
        #     # Отделяем число от команды
        #     m = re.search(r'\d+', value)                            # ищем число по регулярному выражению
        #     if not m:                                               # если не нашел
        #         raise Exception(f"Not found number.")               # выдаем эксепшен
        #     try:
        #         number = int(m.group())                             # пробуем парсить до целого
        #     except ValueError:                                      # если не получилось
        #         raise Exception('Some issues with the number!!!')  # выдаем эксепшен
            
        #     result_val  = 0x0   # переменная в которой мы формируем значение

        #     # Обработка остатка или формирование команды с малым значениес (1 байт)
        #     if number > 0 and number <= 0xFF:                                               # если осталось малое число 1...255             
        #         result_val = (side << 8) | (number & 0xFF)
        #         number -= number   # обнуляем остаток
        #         temp_cmd = build_modbus_cmd(cmd_array["modbus"], override_value=result_val)
        #         send_cmd.append(temp_cmd)
            
        #     if number != 0:
        #         raise Exception(f'Some remainder: {number}')

        if len(send_cmd) < 1:
            raise Exception('Device commands not generated!')
        
        original_timeout = ser.timeout
        ser.timeout = 3.0

        for sending in send_cmd:
            # Логирование отправляемых байт
            send_hex = binascii.hexlify(sending).decode('utf-8').upper()
            send_hex_f = " ".join(send_hex[i:i+2] for i in range(0, len(send_hex), 2))
            print(f'Send bytes: {send_hex_f}')

            # Отправляем команду
            ser.write(sending)

            # Читаем ответ (чаще всего 8 байт для функций 0x05 и 0x06)
            response = ser.read(8)
            response_hex = binascii.hexlify(response).decode('utf-8').upper()
            response_hex_f = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
            
            print(f'Received: {response_hex_f}')

            # Проверяем CRC в ответе
            if not valid_crc16(response):
                raise Exception(f'Invalid CRC16! Received: {response_hex_f}')

            # Дополнительно можно проверить, что первые 6 байт совпадают
            # (адрес, функция, регистр, значение) — здесь send_cmd[:6]
            # Часто контроллер возвращает тот же набор, если команда принята.
            if sending[:6] in response:
                print(f'Command [{cmd}] done!')
            else:
                raise Exception(f'Some issues with {cmd}')
            
        ser.timeout = original_timeout

    elif cmd == "rtc":
        if value is None:
            print(f'> Set the data with local time from OS.')
            current_time = time.localtime()  # Получаем текущую дату
            
            print(f'> Minutes: {(current_time.tm_min)}; Seconds: {current_time.tm_sec}')
            min_sec = (current_time.tm_min << 8) | current_time.tm_sec
            print(f'> Value: {min_sec} (0x{min_sec:04X})')

            send_and_get(cmd_array, 8, ser, ov_reg=commands.REG.REG_RTC_MIN_SEC, ov_value=min_sec)

            while ser.in_waiting:
                ser.read(20)

            print(f'> Date: {(current_time.tm_mday)}; Hours: {current_time.tm_hour}')
            date_hour = (current_time.tm_mday << 8) | current_time.tm_hour
            print(f'> Value: {date_hour} (0x{date_hour:04X})')

            send_and_get(cmd_array, 8, ser, ov_reg=commands.REG.REG_RTC_DATE_HOUR, ov_value=date_hour)

            while ser.in_waiting:
                ser.read(20)

            print(f'> Year: {(current_time.tm_year - 2000)}; Month: {current_time.tm_mon}')
            year_month = ((current_time.tm_year - 2000) << 8) | current_time.tm_mon
            print(f'> Value: {year_month} (0x{year_month:04X})')
            
            send_and_get(cmd_array, 8, ser, ov_value=year_month)

            print("========================================")

        else:
            print(f'> Set the data with value: {value}')
            yy = None
            mm = None
            dd = None
            hh = None
            min = None
            sec = None

            m = re.search(r'^(\d+)\.', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    dd = int(m.group()[:-1])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')

            dd = dd if dd is not None else None
            m = None

            m = re.search(r'\.(\d+)\.', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    mm = int(m.group()[1:-1])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')

            mm = mm if mm is not None else None
            m = None

            m = re.search(r'\.(\d+)(?!\.)\s', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    yy = int(m.group()[1:])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')

            yy = yy%100 if yy is not None else None
            m = None

            m = re.search(r'\s(?!\:)(\d+)\:', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    hh = int(m.group()[:-1])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')

            hh = hh if hh is not None else None
            m = None

            m = re.search(r'\:(\d+)\:', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    min = int(m.group()[1:-1])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')

            min = min if min is not None else None
            m = None

            m = re.search(r'\:(\d+)(?!\:|\d+)', value)                            # ищем число по регулярному выражению
            if m is not None:                                               # если не нашел
                try:
                    # print(f'm: {m.group()}')
                    sec = int(m.group()[1:])                             # пробуем парсить до целого
                except ValueError as ve:                                      # если не получилось
                    print(f'[WARN] Year Value Error: {ve}')
 
            sec = sec if sec is not None else None
            m = None

            print(f'>>> Parsed Data: {dd:02}.{mm:02}.{yy:02} {hh:02}:{min:02}:{sec:02}')

            if min is not None and sec is not None:
                min_sec = (min << 8) | sec
                print(f'>>> min_sec: 0x{min_sec:02X}')
                send_and_get(cmd_array, 8, ser, ov_reg=commands.REG.REG_RTC_MIN_SEC, ov_value=min_sec)

            while ser.in_waiting:
                ser.read(20)

            if dd is not None and hh is not None:
                dd_hh = (dd << 8) | hh
                print(f'>>> dd_hh: 0x{dd_hh:02X}')
                send_and_get(cmd_array, 8, ser, ov_reg=commands.REG.REG_RTC_DATE_HOUR, ov_value=dd_hh)

            while ser.in_waiting:
                ser.read(20)

            if yy is not None and mm is not None:
                yy_mm = (yy << 8) | mm
                print(f'>>> yy_mm: 0x{yy_mm:02X}')
                send_and_get(cmd_array, 8, ser, ov_value=yy_mm)

            print("========================================")

    else:
        if value == "default":
            tmp_value = None
        elif value is not None:
            try:
                tmp_value = int(value)  # пробуем парсить до целого
            except ValueError:          # если не получилось
                raise Exception(f'Value should be a number or "default"!!! Your: {value}')  # выдаем эксепшен

        # print(f'{tmp_value}')
        tmp_cmd = build_modbus_cmd(cmd_array["modbus"], override_value=tmp_value)
        # print(f'{tmp_cmd}')
        response = send_and_get(cmd_array, 8, ser, ov_value=tmp_value)

        if tmp_cmd[:6] in response:
            text_result = "========================================\n"
            text_result += f'  >>> {cmd_array["title"]}: {tmp_value if value != "default" else "default"} [{cmd_array["units"]}] <<<\n'
            text_result += "========================================"
            print(f'{text_result}')
        else:
            raise Exception(f'Some issues with {cmd}!')

    # pass # Заглушка

def my_bytes_with_serial(baudrate, serial_port, bytes_str: str, crc_flag: bool | None = False):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        func_my_bytes(bytes_str, ser, crc_flag)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

# Отправляем любые байты по COM-порту
def func_my_bytes(bytes_str: str, ser, crc_flag: bool | None = False):
    '''
    Данная функция сделана для того, чтобы можно было произвольному устройству по
    COM-порту "не отходя от кассы" отправить пачку байт 
    '''
    # Удаляем лишние пробелы по краям
    hex_string = bytes_str.strip().upper()

    # Проверка: строка должна содержать байты в формате "XX XX XX"
    if not re.fullmatch(r'([0-9A-F]{2})( [0-9A-F]{2})*', hex_string):
        raise ValueError("Invalid string format. Expected: 'XX XX XX', where XX are bytes in hexadecimal.")

    # Преобразуем строку в набор байт
    bytes_from_str = bytes.fromhex(hex_string)

    if len(bytes_from_str) >= 3 and crc_flag:
        # Считаем CRC16
        crc = crc16(bytes_from_str)
        bytes_from_str = bytes_from_str + crc.to_bytes(2,"big")

    if len(bytes_from_str) > 200:
        raise Exception("Should be less than 200 bytes!!!")

    # Логирование отправляемых байт
    send_hex = binascii.hexlify(bytes_from_str).decode('utf-8').upper()
    send_hex_f = " ".join(send_hex[i:i+2] for i in range(0, len(send_hex), 2))
    print(f'Send bytes: {send_hex_f}')

    # Отправляем команду
    ser.write(bytes_from_str)

    # Читаем ответ
    response = ser.read(255)
    response_hex = binascii.hexlify(response).decode('utf-8').upper()
    response_hex_f = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
    
    # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
    while ser.in_waiting:
        ser.read(20)

    print(f'Received: {response_hex_f}')

    # Проверяем CRC в ответе
    if not valid_crc16(response):
        raise Exception(f'Invalid CRC16! Received: {response_hex_f}')


# def connect_to_port(baudrate, port):
#     try:
#         ser = serial.Serial(
#             port        = port,
#             baudrate    = baudrate,
#             parity      = serial.PARITY_NONE,
#             stopbits    = serial.STOPBITS_ONE,
#             bytesize    = serial.EIGHTBITS,
#             timeout     = 0.5  # Таймаут чтения в секундах
#         )
#         print(f"\n==== Successfully connected to {port} ====")
#         return ser

#     except serial.SerialException as e:
#         # Проверяем текст ошибки
#         if "FileNotFoundError" in str(e):
#             print(f"FileNotFoundError: Port {port} not found.")
#         else:
#             print(f"Serial exception: {e}")
#         return None

# Собираем посылку по команде
def build_modbus_cmd(
        modbus_dict: commands.ModbusDict,
        override_address: int | None = None,
        override_function: int | None = None,
        override_register: int | None = None,
        override_value: int | None = None
    ) -> bytes:
    """
    Формирует байтовую строку Modbus-запроса (6 байт) + 2 байта CRC16.
    Пример: [address, function, reg_hi, reg_lo, val_hi, val_lo, crc_hi, crc_lo]
    """
    address     = override_address if override_address is not None else modbus_dict["address"]
    function    = override_function if override_function is not None else modbus_dict["function"]
    register    = override_register if override_register is not None else modbus_dict["register"]
    value       = override_value if override_value is not None else modbus_dict["value"]
    value       = value & 0xFFFF  # Гарантия, что это uint16 (для передачи отрицательных значений)

    # Ограничиваем полученные значения соразмерно байтам
    address     = min(max(address, 0), 0xFF)    # Если меньше 0 → 0, если больше 255 → 255
    function    = min(max(function, 0), 0xFF)   # Если меньше 0 → 0, если больше 255 → 255
    register    = min(max(register, 0), 0xFFFF) # Если меньше 0 → 0, если больше 65535 → 65535
    value       = min(max(value, 0), 0xFFFF)    # Если меньше 0 → 0, если больше 65535 → 65535

    # Собираем команду (без CRC)
    raw_cmd = (
        address.to_bytes(1,"big") +
        function.to_bytes(1,"big") +
        register.to_bytes(2,"big") +
        value.to_bytes(2,"big")
    )
    # Считаем CRC16
    crc = crc16(raw_cmd)

    return raw_cmd + crc.to_bytes(2,"big")

def crc16(buffer):
    crc_hi = 0xFF  # High CRC byte
    crc_lo = 0xFF  # Low CRC byte
    for byte in buffer:
        i = crc_hi ^ byte
        crc_hi = crc_lo ^ table_crc_hi[i]
        crc_lo = table_crc_lo[i]
    return (crc_hi << 8) | crc_lo

def test_with_serial(baudrate, serial_port, cmd: str):
    import serial

    try:
        ser = serial.Serial(
            port        = serial_port,
            baudrate    = baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            timeout     = 0.5  # Таймаут чтения в секундах
        )
        print(f"==== Successfully connected to {serial_port} ====")

        # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
        while ser.in_waiting:
            ser.read(20)

        test(cmd, ser)

    except serial.SerialException as e:
        # Проверяем текст ошибки
        if "FileNotFoundError" in str(e):
            print(f"FileNotFoundError: Port {serial_port} not found.")
        else:
            print(f"Serial exception: {e}")

    finally:
        ser.close()

def test(cmd: str, ser):

    match cmd:
        case "leds":
            print("=========== Let's test LEDs ===========")
            print("[CHECK] >>> LED1 (H2) - light ON")
            func_control("led1_on", ser)
            print("[CHECK] >>> LED1 (H2) - light blinking 1 second then stay lighting")
            func_control("led1_1s", ser)
            print("[CHECK] >>> LED1 (H2) - light OFF")
            func_control("led1_off", ser)
            print("[CHECK] >>> LED1 (H2) - light blinking 2 second then the lights go out")
            func_control("led1_2s", ser)
            print("[CHECK] >>> LED2 (H3) - light ON")
            func_control("led2_on", ser)
            print("[CHECK] >>> LED2 (H3) - light blinking 1 second then stay lighting")
            func_control("led2_1s", ser)
            print("[CHECK] >>> LED2 (H3) - light OFF")
            func_control("led2_off", ser)
            print("[CHECK] >>> LED2 (H3) - light blinking 1 second then stay lighting")
            func_control("led2_2s", ser)
            print(">>> Done!")

        case "flash":
            # нижнюю температуру
            value_lo = "-11"    # как текст, потому что такое значение
            value_hi = "111"    # принимают основные функции

            print(f'Setted: value_lo - "{value_lo}"; value_hi - "{value_hi}"')

            ''' Сначала читаем значения параметров '''
            func_read("start_temp", ser)

            ''' Меняем первое значение '''
            func_write("start_low_temp", ser, value=value_lo)

            ''' Меняем второе значение '''
            func_write("start_high_temp", ser, value=value_hi)

            ''' Читаем снова значения параметров '''
            func_read("start_temp", ser)

            ''' Записываем новые параметры во Flash '''
            func_control("params_save", ser)

            time.sleep(2.0) # выдерживаем паузу

            ''' Сбрасываем МК '''
            func_control("reset", ser)

            print('> Wait 15 sec...')
            time.sleep(15.0) # выдерживаем паузу, даём прошивке загрузиться полноценно

            # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
            while ser.in_waiting:
                ser.read(20)

            ''' Читаем снова значения параметров '''
            func_read("start_temp", ser)

            ''' Устанавливает деволтные и записываем'''
            func_control("params_reset", ser)

            ''' Снова читаем '''
            func_read("start_temp", ser)

            text_result = "========================================\n"
            text_result += f'  >>> Tests done!!! Check the iteration log!!!  <<<\n'
            text_result += "========================================"
            print(f'{text_result}')

        case "sensors":
            print("Sensors Tests Sarts")

            # Сначала проверяем все параметры входного датчика
            # читаем напряжение
            func_read("in_v", ser)
            # читаем ток
            func_read("in_i", ser)
            # читаем напряжение шунта
            func_read("in_v_shunt", ser)
            # читаем потребление
            func_read("accum", ser)

            time.sleep(10)

            # Потом данные с датчика радара
            # читаем напряжение
            # read_new("ra_v", ser)
            # # читаем ток
            # read_new("ra_i", ser)
            # # читаем напряжение шунта
            # read_new("ra_v_shunt", ser)

            # time.sleep(10)

            # Потом с датчика ПК
            # читаем напряжение
            func_read("pc_v", ser)
            # читаем ток
            func_read("pc_i", ser)
            # читаем напряжение шунта
            func_read("pc_v_shunt", ser)
            
            print('========================================')

            time.sleep(10)

            # Потом с датчика драйвера прожектора
            # читаем напряжение
            func_read("sl_v", ser)
            # читаем ток
            func_read("sl_i", ser)
            # читаем напряжение шунта
            func_read("sl_v_shunt", ser)

            print('========================================')

            time.sleep(60)

            # читаем потребление
            func_read("accum", ser)
        case "motors":

            # ser.timeout = 0.0
            ''' В ПРОЕКТЕ '''
            func_control("version_request", ser)
            func_my_bytes("30 06 20 12 83 0C", ser, crc_flag=True)
            func_my_bytes("30 06 20 12 03 68", ser, crc_flag=True)
            func_control("version_request", ser)
            func_my_bytes("30 06 20 12 03 50", ser, crc_flag=True)
            func_control("version_request", ser)
            func_my_bytes("30 06 20 12 82 0A", ser, crc_flag=True)
            func_my_bytes("30 06 20 12 02 B0", ser, crc_flag=True)
            func_control("version_request", ser)

        case "motors_2":
            for i in range(20):
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                # while ser.in_waiting:
                #     ser.read(20)
                print(f'COUNT #{i+1}')
                func_write("focus", ser, value=">255")
                time.sleep(0.3)
                func_write("focus", ser, value="<255")
                time.sleep(0.3)
                

        case "work":
            time.sleep(10.0)

            # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
            while ser.in_waiting:
                ser.read(20)

            func_read("version_request", ser)
            time.sleep(5.0)
            func_control("led1_2hz", ser)
            time.sleep(0.05)
            value = ">4000"
            for i in range(400): # 400
                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                func_read("version_request", ser)
                time.sleep(0.05)
                func_control("led2_2s", ser)
                time.sleep(0.05)
                func_control("pc_wdt_reset", ser)
                time.sleep(0.1)
                for j in range(5):
                    func_my_bytes("30 03 00 00 00 14", ser, crc_flag=True)
                    func_my_bytes("30 03 00 14 00 14", ser, crc_flag=True)
                    func_my_bytes("30 03 00 28 00 0D", ser, crc_flag=True)
                    time.sleep(1.0)
                time.sleep(5.0)
                if '>' in value:
                    value = "<4000"
                if '<' in value:
                    value = ">4000"
                func_write("focus",ser,value)
                time.sleep(7.0)
                if '>' in value:
                    value = "<4000"
                if '<' in value:
                    value = ">4000"
                func_write("zoom",ser,value)
                time.sleep(7.0)
                if '>' in value:
                    value = "<1000"
                if '<' in value:
                    value = ">1000"
                func_write("diaph",ser,value)
                time.sleep(2.0)

            func_control("led1_off", ser)

        case "imu_data_to_file":
            for i in range(50):
                print(f'READ #{i+1}')
                response    = send_and_get(commands.cmd_read_array['imu'], 29, ser)
                bytes_count = int(response[2])      # Кол-во байт
                imu_data    = response[3:-2]        # Сами данные

                if bytes_count != len(imu_data):
                    raise Exception(f"Number of bytes error: Expected {bytes_count}, but got {len(imu_data)}.")
                
                status  = (imu_data[0] << 8) | imu_data[1]
                gravity = (imu_data[2] << 8) | imu_data[3]
                a_scale = (imu_data[4] << 8) | imu_data[5]
                g_scale = (imu_data[6] << 8) | imu_data[7]
                accel_x = (imu_data[8] << 8) | imu_data[9]
                accel_y = (imu_data[10] << 8) | imu_data[11]
                accel_z = (imu_data[12] << 8) | imu_data[13]
                gyro_x  = (imu_data[14] << 8) | imu_data[15]
                gyro_y  = (imu_data[16] << 8) | imu_data[17]
                gyro_z  = (imu_data[18] << 8) | imu_data[19]
                pitch   = (imu_data[20] << 8) | imu_data[21]
                roll    = (imu_data[22] << 8) | imu_data[23]

                # проверяем на отрицательность значения
                if accel_x & 0x8000:    accel_x -= 0x10000
                if accel_y & 0x8000:    accel_y -= 0x10000
                if accel_z & 0x8000:    accel_z -= 0x10000
                if gyro_x & 0x8000:     gyro_x -= 0x10000
                if gyro_y & 0x8000:     gyro_y -= 0x10000
                if gyro_z & 0x8000:     gyro_z -= 0x10000
                if pitch & 0x8000:      pitch -= 0x10000
                if roll & 0x8000:       roll -= 0x10000

                match status:
                    case 0:
                        text_status = 'ICM_FIRST_START'
                    case 1:
                        text_status = 'ICM_OK'
                    case 2:
                        text_status = 'ICM_ERR_NOT_RESP'
                    case 3:
                        text_status = 'ICM_ERR_WHO_AM_I'
                    case 4:
                        text_status = 'ICM_ERR_RESET'
                    case 5:
                        text_status = 'ICM_ERR_CLK'
                    case 6:
                        text_status = 'ICM_ERR_SLEEP_MODE'
                    case 7:
                        text_status = 'ICM_ERR_INTERFACE'
                    case 8:
                        text_status = 'ICM_ERR_TO_BANK2'
                    case 9:
                        text_status = 'ICM_ERR_GYRO_DIV'
                    case 10:
                        text_status = 'ICM_ERR_GYRO_CFG1'
                    case 11:
                        text_status = 'ICM_ERR_GYRO_CFG2'
                    case 12:
                        text_status = 'ICM_ERR_ACCEL_DIV'
                    case 13:
                        text_status = 'ICM_ERR_ACCEL_CFG1'
                    case 14:
                        text_status = 'ICM_ERR_ACCEL_CFG2'
                    case 15:
                        text_status = 'ICM_ERR_TO_BANK0'
                    case 16:
                        text_status = 'ICM_ERR_ACCEL_GYRO_ON'
                    case 17:
                        text_status = 'ICM_BUSY'
                    case _:
                        text_status = 'unknown'

                text_result = "========================================\n"
                text_result += f'Status ICM-20948 Initialization: {text_status}\n'
                text_result += f'Gravitational Acceleration: {(gravity/1000):.3f} [m/c2]\n'
                text_result += f"Accelerometer Scale: a_scale={a_scale} (g*a_scale in MCU)\n"
                text_result += f'Gyroscope Scale: g_scale={g_scale} (dps*g_scale in MCU)\n'
                text_result += "========================================\n"
                text_result += "    Putting to file...\n"
                text_result += "========================================"
                print(f'{text_result}')

                """Создание CSV-файла и запись заголовков, если файл пустой или не существует."""
                if not os.path.isfile("imu_data_log.csv") or os.path.getsize("imu_data_log.csv") == 0:
                    with open("imu_data_log.csv", mode="w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(["#", "A_X", "A_Y", "A_Z", "G_X", "G_Y", "G_Z", "PITCH", "ROLL"])

                """Добавление строки с данными IMU."""
                with open("imu_data_log.csv", mode="a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([i+1, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, pitch, roll])
                time.sleep(10.0)
        # case "imu_10":

                # global work_index

                # """Создание CSV-файла и запись заголовков, если файл пустой или не существует."""
                # if not os.path.isfile("imu_data_log.csv") or os.path.getsize("imu_data_log.csv") == 0:
                #     with open("imu_data_log.csv", mode="w", newline="") as file:
                #         writer = csv.writer(file)
                #         work_index = 0
                #         writer.writerow(["#", "A_X", "A_Y", "A_Z", "G_X", "G_Y", "G_Z", "PITCH", "ROLL"])

                # """Добавление строки с данными IMU."""
                # with open("imu_data_log.csv", mode="a", newline="") as file:
                #     writer = csv.writer(file)
                #     work_index += 1
                #     writer.writerow([work_index, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, pitch, roll])

            # case "imu_to_file":
            #     # 5 байт всегда + данные
            #     resp_status = send_and_get("imu_status", 17, ser)
            #     resp_data_1 = send_and_get("imu_data_1", 95, ser)
            #     resp_data_2 = send_and_get("imu_data_2", 95, ser)
            #     resp_data_3 = send_and_get("imu_data_3", 95, ser)
            #     resp_data_4 = send_and_get("imu_data_4", 95, ser)
            #     resp_data_5 = send_and_get("imu_data_5", 95, ser)
            #     resp_data_6 = send_and_get("imu_data_6", 95, ser)

            #     # Разбираем посылку
            #     imu_status_bytes    = int(resp_status[2])      # Кол-во байт
            #     imu_status_data     = resp_status[3:-2]        # Сами данные
            #     imu_data_1_bytes    = int(resp_data_1[2])      # Кол-во байт
            #     imu_data_1          = resp_data_1[3:-2]        # Сами данные
            #     imu_data_2_bytes    = int(resp_data_2[2])      # Кол-во байт
            #     imu_data_2          = resp_data_2[3:-2]        # Сами данные
            #     imu_data_3_bytes    = int(resp_data_3[2])      # Кол-во байт
            #     imu_data_3          = resp_data_3[3:-2]        # Сами данные
            #     imu_data_4_bytes    = int(resp_data_4[2])      # Кол-во байт
            #     imu_data_4          = resp_data_4[3:-2]        # Сами данные
            #     imu_data_5_bytes    = int(resp_data_5[2])      # Кол-во байт
            #     imu_data_5          = resp_data_5[3:-2]        # Сами данные
            #     imu_data_6_bytes    = int(resp_data_6[2])      # Кол-во байт
            #     imu_data_6          = resp_data_6[3:-2]        # Сами данные

            #     # Проверка длинны
            #     if imu_status_bytes != len(imu_status_data):
            #         raise Exception(f"Number of bytes error: Expected {imu_status_bytes}, but got {len(imu_status_data)}.")
            #     if imu_data_1_bytes != len(imu_data_1):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_1_bytes}, but got {len(imu_data_1)}.")
            #     if imu_data_2_bytes != len(imu_data_2):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_2_bytes}, but got {len(imu_data_2)}.")
            #     if imu_data_3_bytes != len(imu_data_3):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_3_bytes}, but got {len(imu_data_3)}.")
            #     if imu_data_4_bytes != len(imu_data_4):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_4_bytes}, but got {len(imu_data_4)}.")
            #     if imu_data_5_bytes != len(imu_data_5):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_5_bytes}, but got {len(imu_data_5)}.")
            #     if imu_data_6_bytes != len(imu_data_6):
            #         raise Exception(f"Number of bytes error: Expected {imu_data_6_bytes}, but got {len(imu_data_6)}.")

            #     status      = (imu_status_data[0] << 8) | imu_status_data[1]
            #     gravity     = (imu_status_data[2] << 8) | imu_status_data[3]
            #     a_scale     = (imu_status_data[4] << 8) | imu_status_data[5]
            #     g_scale     = (imu_status_data[6] << 8) | imu_status_data[7]
            #     buf_size    = (imu_status_data[8] << 8) | imu_status_data[9]
            #     buf_index   = (imu_status_data[10] << 8) | imu_status_data[11]

            #     match status:
            #         case 0:
            #             text_status = 'ICM_FIRST_START'
            #         case 1:
            #             text_status = 'ICM_OK'
            #         case 2:
            #             text_status = 'ICM_ERR_NOT_RESP'
            #         case 3:
            #             text_status = 'ICM_ERR_WHO_AM_I'
            #         case 4:
            #             text_status = 'ICM_ERR_RESET'
            #         case 5:
            #             text_status = 'ICM_ERR_CLK'
            #         case 6:
            #             text_status = 'ICM_ERR_SLEEP_MODE'
            #         case 7:
            #             text_status = 'ICM_ERR_INTERFACE'
            #         case 8:
            #             text_status = 'ICM_ERR_TO_BANK2'
            #         case 9:
            #             text_status = 'ICM_ERR_GYRO_DIV'
            #         case 10:
            #             text_status = 'ICM_ERR_GYRO_CFG1'
            #         case 11:
            #             text_status = 'ICM_ERR_GYRO_CFG2'
            #         case 12:
            #             text_status = 'ICM_ERR_ACCEL_DIV'
            #         case 13:
            #             text_status = 'ICM_ERR_ACCEL_CFG1'
            #         case 14:
            #             text_status = 'ICM_ERR_ACCEL_CFG2'
            #         case 15:
            #             text_status = 'ICM_ERR_TO_BANK0'
            #         case 16:
            #             text_status = 'ICM_ERR_ACCEL_GYRO_ON'
            #         case 17:
            #             text_status = 'ICM_BUSY'
            #         case _:
            #             text_status = 'unknown'

            #     text_result = "========================================\n"
            #     text_result += f'Status ICM-20948 Initialization: {text_status}\n'
            #     text_result += f'Gravitational Acceleration: {(gravity/1000):.3f} [m/c2]\n'
            #     text_result += f"Accelerometer Scale: a_scale={a_scale} (g*a_scale in MCU)\n"
            #     text_result += f'Gyroscope Scale: g_scale={g_scale} (dps*g_scale in MCU)\n'
            #     text_result += f'Buffer Size: {buf_size}\n'
            #     text_result += f'Next index for save: {buf_index}\n'

            #     text_result += "========================================"
            #     print(f'{text_result}')

            #     """Создание CSV-файла и запись заголовков, если файл пустой или не существует."""
            #     if not os.path.isfile("imu_data_log.csv") or os.path.getsize("imu_data_log.csv") == 0:
            #         with open("imu_data_log.csv", mode="w", newline="") as file:
            #             writer = csv.writer(file)
            #             writer.writerow(["A_X", "A_Y", "A_Z", "G_X", "G_Y", "G_Z", "TEMP", "TIME"])

            #     """Добавление строки с данными IMU."""
            #     # Part 1
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_1[0+offset] << 8) | imu_data_1[1+offset]
            #             accel_y     = (imu_data_1[2+offset] << 8) | imu_data_1[3+offset]
            #             accel_z     = (imu_data_1[4+offset] << 8) | imu_data_1[5+offset]
            #             gyro_x      = (imu_data_1[6+offset] << 8) | imu_data_1[7+offset]
            #             gyro_y      = (imu_data_1[8+offset] << 8) | imu_data_1[9+offset]
            #             gyro_z      = (imu_data_1[10+offset] << 8) | imu_data_1[11+offset]
            #             imu_temp    = (imu_data_1[12+offset] << 8) | imu_data_1[13+offset]
            #             timer_ms    = (imu_data_1[14+offset] << 24) | (imu_data_1[15+offset] << 16) | (imu_data_1[16+offset] << 8) | imu_data_1[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])

            #     # Part 2
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_2[0+offset] << 8) | imu_data_2[1+offset]
            #             accel_y     = (imu_data_2[2+offset] << 8) | imu_data_2[3+offset]
            #             accel_z     = (imu_data_2[4+offset] << 8) | imu_data_2[5+offset]
            #             gyro_x      = (imu_data_2[6+offset] << 8) | imu_data_2[7+offset]
            #             gyro_y      = (imu_data_2[8+offset] << 8) | imu_data_2[9+offset]
            #             gyro_z      = (imu_data_2[10+offset] << 8) | imu_data_2[11+offset]
            #             imu_temp    = (imu_data_2[12+offset] << 8) | imu_data_2[13+offset]
            #             timer_ms    = (imu_data_2[14+offset] << 24) | (imu_data_2[15+offset] << 16) | (imu_data_2[16+offset] << 8) | imu_data_2[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])

            #     # Part 3
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_3[0+offset] << 8) | imu_data_3[1+offset]
            #             accel_y     = (imu_data_3[2+offset] << 8) | imu_data_3[3+offset]
            #             accel_z     = (imu_data_3[4+offset] << 8) | imu_data_3[5+offset]
            #             gyro_x      = (imu_data_3[6+offset] << 8) | imu_data_3[7+offset]
            #             gyro_y      = (imu_data_3[8+offset] << 8) | imu_data_3[9+offset]
            #             gyro_z      = (imu_data_3[10+offset] << 8) | imu_data_3[11+offset]
            #             imu_temp    = (imu_data_3[12+offset] << 8) | imu_data_3[13+offset]
            #             timer_ms    = (imu_data_3[14+offset] << 24) | (imu_data_3[15+offset] << 16) | (imu_data_3[16+offset] << 8) | imu_data_3[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])

            #     # Part 4
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_4[0+offset] << 8) | imu_data_4[1+offset]
            #             accel_y     = (imu_data_4[2+offset] << 8) | imu_data_4[3+offset]
            #             accel_z     = (imu_data_4[4+offset] << 8) | imu_data_4[5+offset]
            #             gyro_x      = (imu_data_4[6+offset] << 8) | imu_data_4[7+offset]
            #             gyro_y      = (imu_data_4[8+offset] << 8) | imu_data_4[9+offset]
            #             gyro_z      = (imu_data_4[10+offset] << 8) | imu_data_4[11+offset]
            #             imu_temp    = (imu_data_4[12+offset] << 8) | imu_data_4[13+offset]
            #             timer_ms    = (imu_data_4[14+offset] << 24) | (imu_data_4[15+offset] << 16) | (imu_data_4[16+offset] << 8) | imu_data_4[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])

            #     # Part 5
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_5[0+offset] << 8) | imu_data_5[1+offset]
            #             accel_y     = (imu_data_5[2+offset] << 8) | imu_data_5[3+offset]
            #             accel_z     = (imu_data_5[4+offset] << 8) | imu_data_5[5+offset]
            #             gyro_x      = (imu_data_5[6+offset] << 8) | imu_data_5[7+offset]
            #             gyro_y      = (imu_data_5[8+offset] << 8) | imu_data_5[9+offset]
            #             gyro_z      = (imu_data_5[10+offset] << 8) | imu_data_5[11+offset]
            #             imu_temp    = (imu_data_5[12+offset] << 8) | imu_data_5[13+offset]
            #             timer_ms    = (imu_data_5[14+offset] << 24) | (imu_data_5[15+offset] << 16) | (imu_data_5[16+offset] << 8) | imu_data_5[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])

            #     # Part 6
            #     with open("imu_data_log.csv", mode="a", newline="") as file:
            #         writer = csv.writer(file)
            #         for i in range(5):
            #             offset = 18 * i

            #             accel_x     = (imu_data_6[0+offset] << 8) | imu_data_6[1+offset]
            #             accel_y     = (imu_data_6[2+offset] << 8) | imu_data_6[3+offset]
            #             accel_z     = (imu_data_6[4+offset] << 8) | imu_data_6[5+offset]
            #             gyro_x      = (imu_data_6[6+offset] << 8) | imu_data_6[7+offset]
            #             gyro_y      = (imu_data_6[8+offset] << 8) | imu_data_6[9+offset]
            #             gyro_z      = (imu_data_6[10+offset] << 8) | imu_data_6[11+offset]
            #             imu_temp    = (imu_data_6[12+offset] << 8) | imu_data_6[13+offset]
            #             timer_ms    = (imu_data_6[14+offset] << 24) | (imu_data_6[15+offset] << 16) | (imu_data_6[16+offset] << 8) | imu_data_6[17+offset]

            #             # проверяем на отрицательность значения
            #             if accel_x & 0x8000: accel_x -= 0x10000
            #             if accel_y & 0x8000: accel_y -= 0x10000
            #             if accel_z & 0x8000: accel_z -= 0x10000
            #             if gyro_x & 0x8000: gyro_x -= 0x10000
            #             if gyro_y & 0x8000: gyro_y -= 0x10000
            #             if gyro_z & 0x8000: gyro_z -= 0x10000
            #             if imu_temp & 0x8000: imu_temp -= 0x10000

            #             writer.writerow([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, f"{imu_temp/10:.1f}".replace('.',','), timer_ms])


def func_utility(baudrate, serial_port, cmd: str):

    match cmd:
        case "CP2105_RST":
            # === CP2105 параметры ===
            vid = 0x10C4
            pid = 0xEA70

            ### Windous x64 ###
            if sys.platform.startswith("win"):
                import serial
                import serial.tools.list_ports
                import ctypes
                from ctypes import wintypes

                # === Ищем все порты CP2105 (VID/PID и строка в описании) ===
                all_ports = list(serial.tools.list_ports.comports())
                print(f"\n--- [DEBUG] Detected COM ports ({len(all_ports)}) ---")
                for p in all_ports:
                    print(f"Device: {p.device}")
                    print(f"  Name       : {p.name}")
                    print(f"  Description: {p.description}")
                    print(f"  HWID       : {p.hwid}")
                    print(f"  VID:PID    : {p.vid}:{p.pid}")
                    print(f"  Serial #   : {p.serial_number}")
                    print(f"  Location   : {p.location}")
                    print(f"  Interface  : {p.interface}\n")

                cp2105_ports = [
                    p.device for p in all_ports
                    if p.vid == vid and p.pid == pid
                ]
                print(f"[DEBUG] Found CP2105 ports: {cp2105_ports}")

                if cp2105_ports:
                    print("[INFO] Closing detected CP2105 COM ports (if open)...")

                for port in cp2105_ports:
                    print(f"[INFO] Checking port: {port}")
                    is_open = False
                    try:
                        tmp = serial.Serial(port)
                        is_open = tmp.is_open
                        print(f"  [BEFORE] Port is_open: {is_open}")
                        tmp.close()
                        print(f"  [AFTER ] Port is_open: {tmp.is_open}")
                    except serial.SerialException as se:
                        print(f"  [WARN] SerialException: {se}")
                        continue
                    
                # === Загружаем DLL и находим функции ===
                base = os.path.dirname(__file__)
                dll_path = os.path.join(base, "dll", "CP210xManufacturing.dll")

                if not os.path.isfile(dll_path):
                    print(f"[ERROR] DLL не найдена по пути {dll_path}")
                    return
                else:
                    print(f'[INFO] Path of the CP210xManufacturing.dll: {dll_path}')

                try:
                    dll = ctypes.WinDLL(dll_path)
                    print(f"\n[DEBUG] DLL loaded successfully")

                    # === Пробуем получить указатели на функции ===
                    CP210x_GetNumDevices    = dll.CP210x_GetNumDevices
                    CP210x_Open             = dll.CP210x_Open
                    CP210x_Reset            = dll.CP210x_Reset
                    CP210x_Close            = dll.CP210x_Close

                    print("[DEBUG] DLL functions resolved:")
                    print(f"  CP210x_GetNumDevices    : {CP210x_GetNumDevices}")
                    print(f"  CP210x_Open             : {CP210x_Open}")
                    print(f"  CP210x_Reset            : {CP210x_Reset}")
                    print(f"  CP210x_Close            : {CP210x_Close}")

                    CP210x_GetNumDevices.argtypes = [ctypes.POINTER(wintypes.DWORD)]
                    CP210x_Open.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
                    CP210x_Reset.argtypes = [wintypes.HANDLE]
                    CP210x_Close.argtypes = [wintypes.HANDLE]
                except OSError as oe:
                    print(f'[ERROR] DLL failed: {oe}')
                    return
                except Exception as e:
                    print(f'[ERROR] DLL failed with exception: {e}')
                    return
                
                dev_count   = wintypes.DWORD()
                handle      = wintypes.HANDLE()

                try:
                    # === Получаем количество устройств ===
                    status = CP210x_GetNumDevices(ctypes.byref(dev_count))
                    if status != 0 or dev_count.value == 0:
                        print(f"CP210x_GetNumDevices failed. Status: {status}, Devices found: {dev_count.value}")
                        return
                    
                    print(f"[DEBUG] Devices found: {dev_count.value}. Status: {status}")

                    # === Открываем первое устройство (индекс 0) ===
                    status = CP210x_Open(0, ctypes.byref(handle))
                    if status != 0:
                        print(f"[ERROR] CP210x_Open failed. Status: {status}")
                        return

                    print(f"[DEBUG] Device opened successfully. HANDLE: {handle.value}")

                    # === Ресетим ===
                    status = CP210x_Reset(handle)
                    if status == 0:
                        print(f"[INFO] Reset command sent successfully. Status: {status}")
                    else:
                        print(f"[ERROR] Reset failed. Status: {status}")

                finally:
                    if handle.value:
                        # === Закрываем дескриптор ===
                        status = CP210x_Close(handle)
                        if status == 0:
                            print(f"[DEBUG] Device handle closed. Status: {status}")
                        else:
                            print(f"[ERROR] Failed to close handle. Status: {status}")

            ### Linux ###
            elif sys.platform.startswith("linux"):
                print("[INFO] Linux CP2105 soft-reset via USB")

                import usb.core

                # === Ищем устройство ===
                print('[INFO] Trying to find device')
                dev_raw = usb.core.find(idVendor=vid, idProduct=pid)
                if not isinstance(dev_raw, usb.core.Device):
                    print("[ERROR] CP2105 not found or ambiguous.")
                    return
                dev: usb.core.Device = dev_raw  # теперь безопасно
                if dev is None:
                    print("[ERROR] CP2105 device not found.")
                    return
                    
                # === Получаем описание ===
                print('[INFO] Device was found.')
                
                attached = []
                if dev.is_kernel_driver_active(0):
                    attached.append(0)
                    dev.detach_kernel_driver(0)

                # === Посылаем Reset-запрос ===
                try:
                    print('[INFO] Resetting...')
                    dev.ctrl_transfer(
                        bmRequestType=0x41,   # Host-to-device | Vendor | Device
                        bRequest=0x00,        # CP210x_RESET
                        wValue=0, wIndex=0,   # Стандартные нули
                        data_or_wLength=None,
                        timeout=500
                    )
                except Exception as e:
                    print(f"[ERROR] USB control transfer failed: {e}")
                    print("[HINT] Mb the port is busy or root-rights need.")
                    return
                    
                for intf in attached:
                    try: dev.attach_kernel_driver(intf)
                    except usb.core.USBError as e:
                        print(f"[ERROR] dev.attach_kernel_driver(intf) failed: {e}")
                        
                time.sleep(0.5)
                print("[INFO] Reset command sent.")
            else:
                print("[WARN] Unsupported platform")
        case "back":
            print('> Firmware rollback to factory\nResetting MCU')

            import serial

            try:
                ser = serial.Serial(
                    port        = serial_port,
                    baudrate    = baudrate,
                    parity      = serial.PARITY_NONE,
                    stopbits    = serial.STOPBITS_ONE,
                    bytesize    = serial.EIGHTBITS,
                    timeout     = 0.5  # Таймаут чтения в секундах
                )
                print(f"\n==== Successfully connected to {serial_port} ====")

                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                
                time.sleep(1.0)

                print(f'> Trying send "back" to console by byte (one send, one read etc.)')

                index = 0
                print(f'> Index start: {index}')

                # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                while ser.in_waiting:
                    ser.read(20)

                print(f'> Send byte: {b"b"}')
                ser.write(b"b")
                response = ser.read(1)
                print(f'> Got byte: {response}')
                if response == b"b":
                    index += 1
                time.sleep(0.2)

                print(f'> Send byte: {b"a"}')
                ser.write(b"a")
                response = ser.read(1)
                print(f'> Got byte: {response}')
                if response == b"a":
                    index += 1
                time.sleep(0.2)

                print(f'> Send byte: {b"c"}')
                ser.write(b"c")
                response = ser.read(1)
                print(f'> Got byte: {response}')
                if response == b"c":
                    index += 1
                time.sleep(0.2)

                print(f'> Send byte: {b"k"}')
                ser.write(b"k")
                response = ser.read(1)
                print(f'> Got byte: {response}')
                if response == b"k":
                    index += 1
                time.sleep(0.2)

                print(f'> Index finish: {index}')

                if index == 4:
                    ser.write(b"\n")
                else:
                    time.sleep(1.0)

                    # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                    while ser.in_waiting:
                        ser.read(20)

                    func_control("reset", ser)   # ресетим МК, чтобы перейти в режим консоли

                    # если в этот момент в порт влетают какие-то байты, то мы их читаем, чтобы буфер освободился
                    while ser.in_waiting:
                        ser.read(20)
                        
                    time.sleep(1.0)

                    index = 0

                    print(f'> Send byte: {b"b"}')
                    ser.write(b"b")
                    response = ser.read(1)
                    print(f'> Got byte: {response}')
                    if response == b"b":
                        index += 1
                    time.sleep(0.2)

                    print(f'> Send byte: {b"a"}')
                    ser.write(b"a")
                    response = ser.read(1)
                    print(f'> Got byte: {response}')
                    if response == b"a":
                        index += 1
                    time.sleep(0.2)

                    print(f'> Send byte: {b"c"}')
                    ser.write(b"c")
                    response = ser.read(1)
                    print(f'> Got byte: {response}')
                    if response == b"c":
                        index += 1
                    time.sleep(0.2)

                    print(f'> Send byte: {b"k"}')
                    ser.write(b"k")
                    response = ser.read(1)
                    print(f'> Got byte: {response}')
                    if response == b"k":
                        index += 1
                    time.sleep(0.2)

                    print(f'> Index finish: {index}')

                    if index == 4:
                        ser.write(b"\n")
                    else:
                        time.sleep(1.0)
                        raise Exception(f"Can't back second time")
                
                for i in range(20, -1, -1):  # от 20 до 0
                    print(f'\r\033[33m> Please wait for the system to load: {i} sec\033[0m', end='', flush=True)
                    time.sleep(1)

                print('\n>>> Finished!!! <<<')

            except serial.SerialException as e:
                # Проверяем текст ошибки
                if "FileNotFoundError" in str(e):
                    print(f"FileNotFoundError: Port {serial_port} not found.")
                else:
                    print(f"Serial exception: {e}")

            finally:
                ser.close()

def send_and_get(
        cmd_array,                  # в формате, например для чтения: cmd_array = commands.cmd_read_array[cmd] (где cmd необходимая команда из таблицы cmd_read_array)
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
                ) # создаем команду для отправки, т.е. с CRC16

    # Логирование отправляемых байт
    send_hex = binascii.hexlify(send_cmd).decode('utf-8').upper()
    send_hex_f = " ".join(send_hex[i:i+2] for i in range(0, len(send_hex), 2))
    print(f'> Send bytes: {send_hex_f}')

    ser.write(send_cmd) # отправляем команду МК

    response = ser.read(expected_bytes) # читаем read_bytes байт

    # преобразуем в удобочитаймы формат
    response_hex = binascii.hexlify(response).decode('utf-8').upper()
    response_hex_f = " ".join(response_hex[i:i+2] for i in range(0, len(response_hex), 2))
    
    # пишем ответ в консоль
    print(f'> Received: {response_hex_f}')

    # проверяем целостность данных, что определит к нам фообще команда пришла
    if not valid_crc16(response):
        raise Exception(f'Invalid CRC16! Received: {response_hex_f}')

    # Сразу отметаем, т.к. минимальная посылка - ошибка 5 байт
    if len(response) < 5:
        raise Exception(f"Invalid response length: {len(response)} (expected at least 5 bytes)")
    
    # Проверка соответствия адреса, чтобы на линии мы не поймали команду какого-то другого устройства
    if response[0] != cmd_array["modbus"]["address"]:
        raise Exception(f"Unexpected device address: {hex(response[0])} (expected {hex(cmd_array['modbus']['address'])})")
    
    # проверяем функцию
    if not (response[1] & cmd_array["modbus"]["function"]):
        raise Exception(f"Device returned an error. Code: {hex(response[2])}")

    # Проверка на ошибку (старший бит 0x80)
    if response[1] & 0x80:
        raise Exception(f"Device returned an error. Code: {hex(response[2])}")

    # если длина не соответствует ожидаемой
    if len(response) < expected_bytes:
        raise Exception(f"Invalid response length: {len(response)} (expected {expected_bytes} bytes)")
    
    return response

def get_choices_with_help(cmd_array):
    return {
        name: cmd.get("description", "(no description)")
        for name, cmd in cmd_array.items()
    }

def auto_int(x):
    return int(x, 0)  # автоматически определяет основание (0x..., 0b..., 0...)

def main():
    
    # Создаем парсер для основной команды
    parser = argparse.ArgumentParser(description="Console App for Small Edge.")

    subparsers = parser.add_subparsers(dest="type", required=True)

    # Общие аргументы, которые будут использоваться во всех подкомандах
    common_parser = argparse.ArgumentParser(add_help=False)
    # common_parser.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")
    common_parser.add_argument("-b", "--baudrate", type=int, choices=[9600, 19200, 38400, 57600, 115200], default=19200, help="Connection baudrate (Default: 19200)")

    # READ
    parser_read = subparsers.add_parser("read", parents=[common_parser], help="Read from device", formatter_class=RawTextHelpFormatter)
    # parser_read.add_argument("cmd", choices=cmd_array_new.keys(), help="Command name")
    read_choices = get_choices_with_help(commands.cmd_read_array)
    parser_read.add_argument(
        "cmd",
        choices=read_choices.keys(),
        metavar="[command]",
        help="Available commands:\n" + "\n".join(f"  {k:20} {v}" for k, v in read_choices.items())
    )
    parser_read.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    # WRITE
    parser_write = subparsers.add_parser("write", parents=[common_parser], help="Write to and control device with a value", formatter_class=RawTextHelpFormatter)
    write_choices = get_choices_with_help(commands.cmd_write_array)
    parser_write.add_argument(
        "cmd",
        choices=write_choices.keys(),
        metavar="[command]",
        help="Available commands:\n" + "\n".join(f"  {k:20} {v}" for k, v in write_choices.items())
    )
    parser_write.add_argument("-v", "--value", default=None)
    parser_write.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")
 
    # CONTROL
    parser_control = subparsers.add_parser("control", parents=[common_parser], help="Control device", formatter_class=RawTextHelpFormatter)
    control_choices = get_choices_with_help(commands.cmd_control_array)
    parser_control.add_argument(
        "cmd",
        choices=control_choices.keys(),
        metavar="[command]",
        help="Available commands:\n" + "\n".join(f"  {k:20} {v}" for k, v in control_choices.items())
    )
    parser_control.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    # TEST
    parser_test = subparsers.add_parser("test", parents=[common_parser], help="Run tests", formatter_class=RawTextHelpFormatter)
    test_choices = get_choices_with_help(commands.cmd_test_array)
    parser_test.add_argument(
        "cmd",
        choices=test_choices.keys(),
        metavar="[command]",
        help="Available commands:\n" + "\n".join(f"  {k:20} {v}" for k, v in test_choices.items())
    )
    parser_test.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    # MY BYTES
    parser_my_bytes = subparsers.add_parser("my_bytes", parents=[common_parser], help="Any byte you want (waiting 255 bytes back max)", formatter_class=RawTextHelpFormatter)
    parser_my_bytes.add_argument("--bytes", type=str, metavar=f'["{commands.DEVICE_ADDR_STR} 06 20 00 00 02"]', help="You can set any bytes to device in the text format")
    parser_my_bytes.add_argument("--crc", type=bool, default=False)
    parser_my_bytes.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    # UPDATE
    current_time = time.localtime()                             # Получаем текущую дату
    f_current_time = time.strftime('%d.%m.%y', current_time)    # Форматируем дату

    parser_update = subparsers.add_parser("update", parents=[common_parser], help="Firmware update")
    parser_update.add_argument("-f", "--file", type=str, required=True)
    parser_update.add_argument("-a","--address", type=auto_int, default=commands.DEVICE_ADDR)
    parser_update.add_argument("--date_b", default=f_current_time)
    parser_update.add_argument("--ver_f", default="00.00.00")
    parser_update.add_argument("--date_f", default=f_current_time)
    parser_update.add_argument("--ver_u", default="00.00.00")
    parser_update.add_argument("--date_u", default=f_current_time)
    parser_update.add_argument("-p", "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    # UTILITES
    parser_util = subparsers.add_parser("util", parents=[common_parser], help="Special Utilities", formatter_class=RawTextHelpFormatter)
    util_choices = get_choices_with_help(commands.cmd_util_array)
    parser_util.add_argument(
        "cmd",
        choices=util_choices.keys(),
        metavar="[command]",
        help="Available commands:\n" + "\n".join(f"  {k:20} {v}" for k, v in util_choices.items())
    )
    parser_util.add_argument("-p", "--port", help="Serial port (e.g. COM3 or /dev/ttyUSB1)")

    
    # Разбираем аргументы
    args = parser.parse_args()

    try:
        # Проверка на платформу и настройка пути
        if sys.platform.startswith("win"):
            # Windows
            if not args.port and (args.type != commands.TYPE.UTIL):
                raise ValueError("Port name is required for Windows platform")
            serial_port = args.port     # Например, "COM3"
        elif sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            # Linux/MacOS
            if not args.port and (args.type != commands.TYPE.UTIL):
                raise ValueError("Port name is required for Linux/MacOS")
            serial_port = f"{args.port}"       # Например, "ttyUSB0" → "/dev/ttyUSB0"
        else:
            raise OSError("Unsupported platform")
    except ValueError as ve:
        print(f'Value Error: {ve}')
        sys.exit(1)
    except OSError as oe:
        print(f'OS Error: {oe}')
        sys.exit(1)

    # ser = connect_to_port(args.baudrate, serial_port) # Это переносим в сами функции и используем точечно

    global func_start
    func_start = int(time.time())
    # print(f'Starting time: {func_start}')

    # Проверяем, что запущен Python 3.10 или новее, т.к. build_modbus_cmd имеет более новую реализацию
    if sys.version_info < (3, 10):
        raise Exception("Need Python version 3.10 or more")

    try:
        start_text = '============= START STATUS =============\n'
        start_text += f'Port ---------------------> {args.port}\n'
        start_text += f'Baudrate -----------------> {args.baudrate}\n'
        start_text += f'Type cmd -----------------> {args.type}\n'
        match args.type:
            case commands.TYPE.READ:
                start_text += f'Command ------------------> {args.cmd}\n'
                start_text += f'Command description: {commands.cmd_read_array[args.cmd]["description"]}\n'
                start_text += '========================================'
                print(start_text)
                if commands.TYPE.READ != commands.cmd_read_array[args.cmd]["type"]:
                    raise Exception(f'Incorrect command type! Command type is {commands.cmd_read_array[args.cmd]["type"]}')
                read_with_serial(args.baudrate, serial_port, args.cmd)
                # read_new(args.cmd, ser)
            case commands.TYPE.WRITE:
                start_text += f'Command ------------------> {args.cmd}\n'
                start_text += f'With value ---------------> {args.value}\n'
                start_text += f'Command description: {commands.cmd_write_array[args.cmd]["description"]}\n'
                start_text += '========================================'
                print(start_text)
                if commands.TYPE.WRITE != commands.cmd_write_array[args.cmd]["type"]:
                    raise Exception(f'Incorrect command type! Command type is {commands.cmd_write_array[args.cmd]["type"]}')
                write_with_serial(args.baudrate, serial_port, args.cmd, args.value)
                # write_new(args.cmd, ser, args.value)
            case commands.TYPE.CONTROL:
                start_text += f'Command ------------------> {args.cmd}\n'
                start_text += f'Command description: {commands.cmd_control_array[args.cmd]["description"]}\n'
                start_text += '========================================'
                print(start_text)
                if commands.TYPE.CONTROL != commands.cmd_control_array[args.cmd]["type"]:
                    raise Exception(f'Incorrect command type! Command type is {commands.cmd_control_array[args.cmd]["type"]}')
                control_with_serial(args.baudrate, serial_port, args.cmd)
                # control_new(args.cmd, ser)
            case commands.TYPE.TEST:
                start_text += f'Command ------------------> {args.cmd}\n'
                start_text += f'Command description: {commands.cmd_test_array[args.cmd]["description"]}\n'
                start_text += '========================================'
                print(start_text)
                if commands.TYPE.TEST != commands.cmd_test_array[args.cmd]["type"]:
                    raise Exception(f'Incorrect command type! Command type is {commands.cmd_test_array[args.cmd]["type"]}')
                test_with_serial(args.baudrate, serial_port, args.cmd)
                # test(args.cmd, ser)
            case commands.TYPE.UPDATE:
                start_text += f'File path ----------------> {args.file}\n'
                start_text += f'Date bootloader upload ---> {args.date_b}\n'
                start_text += f'Version factory firmware -> {args.ver_f}\n'
                start_text += f'Date factory firmware ----> {args.date_f}\n'
                start_text += f'Version update firmware --> {args.ver_u}\n'
                start_text += f'Date update firmware -----> {args.date_u}\n'
                start_text += '========================================'
                print(start_text)
                # адрес должен быть 0x01-0xFF
                if args.address < 1 or args.address > 255:
                    raise Exception(f'Incorrect address!!!')
                update_with_serial(args.file, args.baudrate, serial_port, args.date_b, args.ver_f, args.date_f, args.ver_u, args.date_u, args.address)
                # update_new(args.file, ser, args.date_b, args.ver_f, args.date_f, args.ver_u, args.date_u, args.address)
            case "my_bytes":
                if not args.bytes:
                    raise Exception('Not set bytes. See: python controlboard.py my_bytes -h')
                my_bytes_with_serial(args.baudrate, serial_port, args.bytes, args.crc)
                # my_bytes(args.bytes, ser, args.crc)
            case commands.TYPE.UTIL:
                start_text += f'Command ------------------> {args.cmd}\n'
                start_text += f'Command description: {commands.cmd_util_array[args.cmd]["description"]}\n'
                start_text += '========================================'
                print(start_text)
                if commands.TYPE.UTIL != commands.cmd_util_array[args.cmd]["type"]:
                    raise Exception(f'Incorrect command type! Command type is {commands.cmd_util_array[args.cmd]["type"]}')
                func_utility(args.baudrate, serial_port, args.cmd)
    except StopRecursion as e:
        print(f'\033[31m[ERROR] Recursion: {e}\033[0m')
    except Exception as e:
        print(f'\033[31m[ERROR] {e}\033[0m')

    sys.exit(0)

if __name__ == "__main__":
    main()
