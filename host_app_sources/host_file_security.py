from host_settings import *
import os.path
import math


# Эта функция ожидает корректного ввода 4-байтного ключа шифрования от разработчика
def input_key():
    while True:
        user_input = input("Введите 4 байтный ключ шифрования (например, '01020304'): ")
        # Проверить, что введенные данные состоят из 8 шестнадцатеричных символов
        if len(user_input) != 8 or not all(c in "0123456789abcdefABCDEF" for c in user_input):
            print("Ошибка: введите 4 байта в виде 8 шестнадцатеричных символов (например, '01020304').")
        else:
            # Преобразовать введенные данные в беззнаковое 32-битное целое число
            return int(user_input, 16)


# Эта функция открывает зашифрованную прошивку и делит ее на блоки для дальнейшей передачи загрузчику
def open_encrypted_firmware():
    # Число байт прошивки в блоке "данные"
    number_of_bytes_in_data_data = 1024
    result_data_blocks_to_send = []
    try:
        path_to_bin_file = input("Введите путь до прошивки формата .bin: ").strip()
        # path_to_bin_file = "test_app_red_11_04.bin"
        with open(path_to_bin_file, 'rb') as firmware_file:
            print("Файл прошивки успешно открыт, делим ее на блоки")
            firmware_data = firmware_file.read()
            firmware_size = len(firmware_data)
            print("Размер прошивки: " + str(firmware_size) + " байт")
            print("Количество блоков по " + str(number_of_bytes_in_data_data) + " байт: " + str(
                math.ceil(firmware_size / number_of_bytes_in_data_data)))

            for i in range(0, firmware_size, number_of_bytes_in_data_data):
                block_data = firmware_data[i:i + number_of_bytes_in_data_data]
                # Если файл нельзя разделить на блоки нацело, то заполняем оставшиеся в последнем блоке байты
                # числом 0xFF, что является обозначением "чистой" памяти в STM32
                if len(block_data) < number_of_bytes_in_data_data:
                    block_data = block_data.ljust(number_of_bytes_in_data_data, b'\xFF')
                crc = crc32mpeg2_func(data_word + block_data)
                result_data_blocks_to_send.append([data_word, block_data, crc])
        return result_data_blocks_to_send, firmware_size
    except FileNotFoundError:
        print(f"Ошибка open_and_encrypt_firmware: файл '{path_to_bin_file}' не найден")
        exit(0)
    except PermissionError:
        print(f"Ошибка open_and_encrypt_firmware: доступ к файлу '{path_to_bin_file}' запрещен")
        exit(0)
    except Exception as e:
        print(f"Ошибка open_and_encrypt_firmware: {e}")
        exit(0)


# Эта функция шифрует прошивку в формате .bin
def encrypt_firmware_file(encrypt_key):
    try:
        filepath = input("Введите путь до прошивки формата .bin: ").strip()
        with open(filepath, 'rb') as firmware_file:
            firmware_data = firmware_file.read()
            encrypted_data = bytearray(firmware_data)
            for i in range(0, len(firmware_data), 4):
                encrypted_data[i:i + 4] = bytes(
                    [b ^ (encrypt_key >> (8 * (j % 4))) & 0xFF for j, b in enumerate(firmware_data[i:i + 4])])
            encrypted_filename = os.path.splitext(filepath)[0] + '_encrypted.bin'
            with open(encrypted_filename, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            print(f"Файл {filepath} успешно зашифрован в файл {encrypted_filename}")
    except FileNotFoundError:
        print(f"Ошибка encrypt_firmware_file: файл '{filepath}' не найден")
    except PermissionError:
        print(f"Ошибка encrypt_firmware_file: доступ к файлу '{filepath}' запрещен")
    except Exception as e:
        print(f"Ошибка encrypt_firmware_file: {e}")


# Эта функция дешифрует прошивку в формате .bin
def decrypt_firmware_file(encrypt_key):
    try:
        filepath = input("Введите путь до зашифрованной прошивки формата .bin: ").strip()
        with open(filepath, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
            decrypted_data = bytearray(encrypted_data)
            for i in range(0, len(encrypted_data), 4):
                decrypted_data[i:i + 4] = bytes(
                    [b ^ (encrypt_key >> (8 * (j % 4))) & 0xFF for j, b in enumerate(encrypted_data[i:i + 4])])
            decrypted_filename = os.path.splitext(filepath)[0] + '_decrypted.bin'
            with open(decrypted_filename, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data)
            print(f"Файл {filepath} успешно расшифрован в файл {decrypted_filename}")
    except FileNotFoundError:
        print(f"Ошибка decrypt_firmware_file: файл '{filepath}' не найден")
    except PermissionError:
        print(f"Ошибка decrypt_firmware_file: доступ к файлу '{filepath}' запрещен")
    except Exception as e:
        print(f"Ошибка decrypt_firmware_file: {e}")
