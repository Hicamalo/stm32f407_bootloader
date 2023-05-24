import time

from host_file_security import open_encrypted_firmware, input_key
from host_settings import max_usart_connection_try, test_word
from host_uart import send_header, wait_response, send_data, wait_status, send_key


# Эта функция обновления прошивки микроконтроллера
def update_firmware_command(uart_serial):
    try:
        number_of_try_connection = 0

        result_data_blocks_to_send, firmware_size = open_encrypted_firmware()
        print("Отправляю заголовок с размером прошивки")
        while number_of_try_connection < max_usart_connection_try:
            send_header(uart_serial, firmware_size)
            status_of_send_header = wait_status(uart_serial)
            if status_of_send_header == 1:
                print("Заголовок передан успешно")
                break
            elif status_of_send_header == 0 and (number_of_try_connection + 1 == max_usart_connection_try):
                raise Exception("Ошибка при передачи заголовка")
            else:
                number_of_try_connection += 1

        print("Ожидаю ответа о наличии свободного места во flash памяти")
        wait_response(uart_serial)

        print("Начинаю передачу прошивки")
        send_data_result = send_data(uart_serial, result_data_blocks_to_send)

        for i in range(10):
            response = uart_serial.readline().decode("utf-8").strip()
            if response == "Прошивка запрограммирована успешно!":
                print("Прошивка успешно запрограммирована!")
            if response == "Перезагрузка МК!":
                print("Перезагрузка микроконтроллера")

        if send_data_result != 1:
            raise Exception("Ошибка при передаче прошивки")

    except Exception as e:
        print(f"Ошибка update_firmware_command: {e}")
        exit(0)


# Эта функция для смены ключа шифрования прошивки
def set_key_command(uart_serial):
    try:
        number_of_try_connection = 0

        uid = get_uid_command(uart_serial)
        secret_encryption_key = bytes.fromhex(uid[1][2:])  # убираем первые 2 символа "0x"
        secret_encryption_key = int.from_bytes(secret_encryption_key, byteorder="big")
        developer_input_key = input_key()

        developer_input_key = developer_input_key.to_bytes(4, "big")

        # Шифруем ключ при помощи secret_encryption_key
        encrypted_developer_key = bytes(
            [(b ^ (secret_encryption_key >> (8 * (j % 4))) & 0xFF) for j, b in enumerate(developer_input_key)])

        status_result = 0

        while number_of_try_connection < max_usart_connection_try:
            send_key(uart_serial, encrypted_developer_key)
            status_result = wait_status(uart_serial)
            if status_result == 1:
                print("Пакет \"key\" передан успешно!")
                break
            else:
                number_of_try_connection += 1

        if status_result == 0:
            raise Exception("Ошибка при передаче ключа прошивки")

        print("Ожидаю ответа о результате установки ключа шифрования")
        wait_response(uart_serial)

        print_developer_input_key = hex(int.from_bytes(developer_input_key, byteorder="big"))
        print(f"Ключ шифрования - {print_developer_input_key} для МК с UID - {uid[0]}-{uid[1]}-{uid[2]} установлен")

    except Exception as e:
        print(f"Ошибка set_key_command: {e}")
        exit(0)


# Эта функция проверки соответствия ключей шифрования
def check_key_command(uart_serial):
    try:
        number_of_try_connection = 0

        develiper_input_key = input_key()

        # Шифруем тестовое слово полученным ключом шифрования
        encrypted_test_word = bytes(
            [(b ^ (develiper_input_key >> (8 * (j % 4))) & 0xFF) for j, b in enumerate(test_word)])

        status_result = 0

        while number_of_try_connection < max_usart_connection_try:
            send_key(uart_serial, encrypted_test_word)
            status_result = wait_status(uart_serial)
            if status_result == 1:
                print("Пакет \"key\" передан успешно!")
                break
            else:
                number_of_try_connection += 1

        if status_result == 0:
            raise Exception("Ошибка при передаче ключа прошивки")

        print("Ожидаю ответа о соответствии ключей шифрования")
        wait_response(uart_serial)

    except Exception as e:
        print(f"Ошибка check_key_command: {e}")
        exit(0)


# Эта функция нужна для проверки наличия защиты на микроконтроллере
def flash_ob_check_command(uart_serial):
    try:
        number_of_try = 0
        while number_of_try < 5:
            response = uart_serial.readline().decode("utf-8").strip()
            if response == "Защита flash памяти уже включена, отмена команды":
                print('Ответ загрузчика: {}'.format(response))
                exit(0)
            if response == "Защита flash памяти уже выключена, отмена команды":
                print('Ответ загрузчика: {}'.format(response))
                exit(0)
            if response != "":
                print('Ответ загрузчика: {}'.format(response))
                number_of_try += 1
    except Exception as e:
        print(f"Ошибка flash_ob_check_command: {e}")


# Эта функция нужна для установки защиты на flash память
def flash_lock_command(uart_serial):
    try:
        number_of_try = 0
        while number_of_try < 5:
            response = uart_serial.readline().decode("utf-8").strip()
            if response == "Защита flash памяти уже включена, отмена команды":
                exit(0)
            if response == "Ставлю защиту от чтения и записи, через 3 секунды сбросьте питание с устройства":
                print('Ответ загрузчика: {}'.format(response))
                time.sleep(5)
                print("Сбросьте питание с устройства")
                exit(0)
            if response != "":
                print('Ответ загрузчика: {}'.format(response))
                number_of_try += 1
    except Exception as e:
        print(f"Ошибка flash_lock_command: {e}")


# Эта функция нужна для снятия защиты с flash памяти
def flash_unlock_command(uart_serial):
    try:
        number_of_try = 0
        while number_of_try < 5:
            response = uart_serial.readline().decode("utf-8").strip()
            if response == "Отключаю защиту от чтения и записи, через 30 секунд сбросьте питание с устройства и заново запрограммируйте загрузчик":
                print('Ответ загрузчика: {}'.format(response))
                time.sleep(30)
                print("Сбросьте питание с устройства и заново запрограммируйте загрузчик")
                exit(0)
            if response != "":
                print('Ответ загрузчика: {}'.format(response))
                number_of_try += 1
    except Exception as e:
        print(f"Ошибка flash_unlock_command: {e}")


# Эта функция нужна для получения UID микроконтроллера
def get_uid_command(uart_serial):
    try:
        number_of_try_connection = 0

        uid_1 = wait_response(uart_serial)
        uid_2 = wait_response(uart_serial)
        uid_3 = wait_response(uart_serial)

        if uid_1 is not None and uid_2 is not None and uid_3 is not None:
            print(f"UID = {uid_1}-{uid_2}-{uid_3}")
            return uid_1, uid_2, uid_3
        else:
            raise ValueError("UID не может быть пустым")

    except Exception as e:
        print(f"Ошибка uart_serial: {e}")
        exit(0)


# Эта функция нужна для стирания flash памяти с пользовательским приложением
def erase_program_command(uart_serial):
    try:
        number_of_try = 0
        while number_of_try < 5:
            response = uart_serial.readline().decode("utf-8").strip()
            if response != "":
                print('Ответ загрузчика: {}'.format(response))
                number_of_try += 1
    except Exception as e:
        print(f"Ошибка erase_program_command: {e}")


# Эта функция нужна для выбора соответствующей команды для загрузчика (если ее выбирает разработчик)
def execute_develop_bootloader_command(uart_serial, command):
    # Должен соответствовать host_developer_bootloader_commands
    handlers = {
        1: update_firmware_command,
        2: set_key_command,
        3: flash_ob_check_command,
        4: flash_lock_command,
        5: flash_unlock_command,
        6: get_uid_command,
        7: check_key_command,
        8: erase_program_command,
    }

    try:
        handler = handlers.get(command, None)
        if handler is None:
            raise ValueError("Ошибка при выполнении команды - неизвестная команда")

        handler(uart_serial)
    except Exception as e:
        print(f"Ошибка execute_develop_bootloader_command: {e}")
        exit(0)


# Эта функция нужна для выбора соответствующей команды для загрузчика (если ее выбирает пользователь)
def execute_user_bootloader_command(uart_serial, command):
    handlers = {
        1: update_firmware_command,
        2: get_uid_command,
    }

    try:
        handler = handlers.get(command, None)
        if handler is None:
            raise ValueError("Ошибка при выполнении команды - неизвестная команда")

        handler(uart_serial)
    except Exception as e:
        print(f"Ошибка execute_user_bootloader_command: {e}")
        exit(0)
