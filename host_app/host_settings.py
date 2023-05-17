import crcmod

# Начала пакетов
command_word = b"COMD"
header_word = b"HEAD"
data_word = b"DATA"
key_word = b"PASS"
response_word = b"RESP"
test_word = b"TEST"
ack_word = b"ACKW"
nack_word = b"NACK"

bootloader_responses = {"ok": 0xFFFFFFFF,
                        "fail": 0x33333333, }

persons = {
    0: "Разработчик",
    1: "Пользователь"
}

host_user_commands = {
    0: "Выход из программы",
    1: "Загрузить прошивку в микроконтроллер",
    2: "Узнать ID устройства"
}

host_developer_commands = {
    0: "Выход из программы",
    1: "Зашифровать прошивку",
    2: "Расшифровать прошивку",
    3: "Работа с загрузчиком",
}

# Этот словарь должен соответствовать enum cmd_t в файле bootloader_types.h в проекте загрузчика
host_developer_bootloader_commands = {
    0: "Выход из программы",
    1: "Загрузить прошивку в микроконтроллер",
    2: "Сменить ключ шифрования прошивки",
    3: "Проверить наличие защиты flash памяти",
    4: "Заблокировать flash память микроконтроллера",
    5: "Разблокировать flash память микроконтроллер",
    6: "Узнать UID микроконтроллера",
    7: "Проверить соответствие ключей шифрования",
    8: "Очистить flash память с прошивкой",
}

# Максимальное количество попыток связи с загрузчиком
max_usart_connection_try = 10

# Аппаратный блок вычисления CRC в STM32F407 нельзя настроить, он всегда будет вычислять CRC32 по алгоритму MPEG-2
crc32mpeg2_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0xFFFFFFFF, xorOut=0x0, rev=False)
