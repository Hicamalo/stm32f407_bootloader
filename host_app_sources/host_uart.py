import serial
import struct
from serial import *
import serial.tools.list_ports

from host_settings import persons, host_developer_commands, host_developer_bootloader_commands, \
    max_usart_connection_try, crc32mpeg2_func, header_word, response_word, bootloader_responses, data_word, \
    command_word, key_word, host_user_commands


# Вспомогательная функция, чтобы по значению найти ключ словаря
def get_key(val, dictionary):
    for key, value in dictionary.items():
        if val == value:
            return key


# Функция для выбора человека, использующего программу
def input_mode():
    print("Выберите человека, использующего загрузчик:")
    for mode_number, mode_name in persons.items():
        print(f"{mode_number}. {mode_name}")

    while True:
        input_number = input("Введите число: ")
        if not input_number.isnumeric():
            print("Ошибка: введите число")
            continue
        input_number = int(input_number)
        if input_number not in persons:
            print("Ошибка: такого числа нет")
            continue
        break

    return input_number


# Функция для ввода команд от пользователя
def input_user_bootloader_command():
    print("Команды загрузчика:")
    for command_number, command_description in host_user_commands.items():
        print(f"{command_number}. {command_description}")

    while True:
        command_number = input("Введите номер команды: ")
        if not command_number.isnumeric():
            print("Ошибка: введите число")
            continue
        command_number = int(command_number)
        if command_number not in host_user_commands:
            print("Ошибка: такой команды нет")
            continue
        break

    if command_number == 0:
        exit(1)

    return command_number


# Функция для ввода команд от разработчика
def developer_input_command():
    print("Список команд хост программы:")
    for mode_number, mode_description in host_developer_commands.items():
        print(f"{mode_number}. {mode_description}")

    while True:
        command_number = input("Введите номер команды: ")
        if not command_number.isnumeric():
            print("Ошибка: введите число")
            continue
        command_number = int(command_number)
        if command_number not in host_developer_commands:
            print("Ошибка: такой команды нет")
            continue
        break

    if command_number == 0:
        exit(1)

    return command_number


# Функция для ввода команд загрузчику от разработчика
def input_developer_bootloader_command():
    print("Команды загрузчика:")
    for command_number, command_description in host_developer_bootloader_commands.items():
        print(f"{command_number}. {command_description}")

    while True:
        command_number = input("Введите номер команды: ")
        if not command_number.isnumeric():
            print("Ошибка: введите число")
            continue
        command_number = int(command_number)
        if command_number not in host_developer_bootloader_commands:
            print("Ошибка: такой команды нет")
            continue
        break

    if command_number == 0:
        exit(1)

    return command_number


# Функция, которая устанавливает UART соединение с микроконтроллером
def start_uart_connection():
    com_port_finded = False
    baudrate_finded = False
    supported_baudrates = [115200]

    try:
        # Получаем список всех доступных портов в системе
        ports = serial.tools.list_ports.comports()

        if len(ports) == 0:
            raise Exception('На компьютере не найден ни один COM-порт')
        else:
            print("Список доступных COM портов в системе:")
            for port in ports:
                print("Устройство: " + port.device + ". Название: " + port.name + ". Описание: " + port.description)

        while not com_port_finded:
            com_port = input(
                'Пожалуйста, введите название COM-порта (например COM1 для Windows или /dev/ttyS1 для Linux): ')
            com_port = com_port.strip()

            # Итерируемся по списку портов и выводим информацию о каждом из них
            for port in ports:
                if com_port == port.device:
                    com_port_finded = True
                    print('COM-порт найден:', com_port)

            if not com_port_finded:
                print('COM-порт не найден:', com_port)

        while not baudrate_finded:

            delimiter = ', '
            baudrate_string = delimiter.join(str(baudrate) for baudrate in supported_baudrates)

            input_baudrate = input(
                'Пожалуйста, выберите поддерживаемую скорость COM-порта из списка : ' + baudrate_string + '\n')
            input_baudrate = input_baudrate.strip()

            for baudrate in supported_baudrates:
                if int(input_baudrate) == baudrate:
                    baudrate_finded = True
                    print('Установлена скорость:', input_baudrate)

            if not baudrate_finded:
                print('Скорость не поддерживается:', input_baudrate)

        print(
            'Убедитесь, что интефейс USART устройства установлен со следующими настройками: World Length = 8 Bits; Parity = None; Stop Bits = 1;')

        serial_com = serial.Serial(com_port, input_baudrate, EIGHTBITS, PARITY_NONE, STOPBITS_ONE, timeout=15)

        if serial_com.is_open:
            print(f"USART соединение с {serial_com.name} успешно установлено!")
            print(f"Перезагрузите устройство, чтобы начать работать с загрузчиком")
        else:
            raise Exception(f"Ошибка установки USART соединения!")
        return serial_com

    except Exception as e:
        print("Произошла ошибка:", e)
        exit(0)


# Функция, которая ожидает получение пакета типа "статус"
def wait_status(uart_serial):
    try:
        number_of_try = 0
        while number_of_try < max_usart_connection_try:
            response = uart_serial.readline().decode("utf-8").strip()
            index_ackw = response.find("ACKW")
            index_nack = response.find("NACK")
            if index_ackw != -1:
                return 1
            if index_nack != -1:
                return 0
            number_of_try = number_of_try + 1
        return 0
    except Exception as e:
        print(f"Ошибка wait_status: {e}")
        # TODO: нужно ли выходить из программы?


# Функция, которая посылает пакет типа "заголовок"
def send_header(uart_serial, firmware_size):
    try:
        header_data = firmware_size.to_bytes(4, "big")
        header_crc = struct.pack('>I', crc32mpeg2_func(header_word + header_data))
        header_packet = header_word + header_data + header_crc
        uart_serial.write(header_packet)
    except Exception as e:
        print(f"Ошибка send_header: {e}")
        exit(0)


# Функция, которая ожидает получение пакета типа "ответ"
def wait_response(uart_serial):
    number_of_try = 0
    try:
        while number_of_try < max_usart_connection_try:
            number_of_try = number_of_try + 1

            response_packet = uart_serial.readline()
            index = response_packet.find(response_word, 0)
            if index != -1:
                response_data = int.from_bytes(response_packet[4:8], byteorder="little")
                if response_data == bootloader_responses["ok"]:
                    print("Ответ - успех")
                    break
                elif response_data == bootloader_responses["fail"]:
                    raise Exception("Ответ - неудача")
                else:
                    return hex(response_data)
            if number_of_try + 1 == max_usart_connection_try:
                raise ValueError("За все попытки подключения получаем неизвестный ответ")
            number_of_try = number_of_try + 1
    except ValueError as e:
        print(f"Ошибка wait_response: {e}")
        exit(0)


# Функция, которая посылает пакет типа "данные"
def send_data(uart_serial, data_blocks):
    try:
        number_of_try = 0
        number_of_block = 0
        for data_block in data_blocks:
            while number_of_try < max_usart_connection_try:
                time.sleep(0.6)
                data_crc = struct.pack('>I', crc32mpeg2_func(data_word + data_block[1]))
                data_packet = data_word + data_block[1] + data_crc
                uart_serial.write(data_packet)
                status_result = wait_status(uart_serial)

                if status_result == 1:
                    print(f"[{number_of_block + 1} / {len(data_blocks)}]")
                    number_of_block += 1
                    number_of_try = 0
                    break
                elif number_of_try + 1 == max_usart_connection_try:
                    return 0

                number_of_try = number_of_try + 1
        return 1
    except Exception as e:
        print(f"Ошибка send_data: {e}")
        exit(0)


# Функция, которая ожидает переход микроконтроллера в режим загрузчика
def wait_bootloader_mode(uart_serial):
    # Ждем нажатия пользовательской кнопки
    number_of_try = 0
    try:
        while number_of_try < max_usart_connection_try:
            response = uart_serial.readline().decode('utf-8').strip()
            if response != "":
                print('Ответ загрузчика: {}'.format(response))
            if response == 'Кнопка User была нажата, переходим в режим загрузчика':
                print("Кнопка User была нажата, входим в режим загрузчика")
                break
            elif response == 'Кнопка User не нажата, переходим к исполнению пользовательского приложения':
                for i in range(10):
                    response = uart_serial.readline().decode("utf-8").strip()
                    if response != "":
                        print('Ответ загрузчика: {}'.format(response))
                raise Exception("Кнопка User не была нажата")
            elif number_of_try + 1 == max_usart_connection_try:
                raise Exception("Загрузчик не отвечает")
            number_of_try = number_of_try + 1
    except Exception as e:
        print("Ошибка wait_bootloader_mode:", e)
        exit(0)


# Функция, которая посылает пакет типа "команда"
def send_command(uart_serial, command):
    try:
        cmd_cmd = struct.pack(">i", command)
        cmd_crc = struct.pack('>I', crc32mpeg2_func(command_word + cmd_cmd))
        cmd_packet = command_word + cmd_cmd + cmd_crc
        uart_serial.write(cmd_packet)
    except Exception as e:
        print(f"Ошибка send_command: {e}")
        exit(0)


# Функция, которая посылает пакет типа "ключ"
def send_key(uart_serial, key):
    try:
        key_crc = struct.pack('>I', crc32mpeg2_func(key_word + key))
        key_packet = key_word + key + key_crc
        uart_serial.write(key_packet)
    except Exception as e:
        print(f"Ошибка при отправке пакета \"key\": {e}")
        exit(0)
