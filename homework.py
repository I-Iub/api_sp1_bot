import logging
import os
import time

import requests
import telegram
import tg_logger
from dotenv import load_dotenv

load_dotenv()

CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MONTH_TIMESTAMP = 2629743  # месяц в формате timestamp
PARANOID = 13  # см. функцию get_homeworks
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('program.log')
stream_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
# tg_logger отправляет логи в Телеграм
tg_logger.setup(logger, token=TELEGRAM_TOKEN, users=[CHAT_ID])

# инициализируем бота:
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    verdicts = {
        'reviewing': 'Работа взята в ревью',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
    }
    if homework is None:
        return '!Запрос вернул пустые данные!'
    else:
        homework_name = homework.get('homework_name')
        verdict = verdicts.get(homework.get('status'))
        return f'У вас проверили работу "{homework_name}":\n\n{verdict}'


# словарь-хеш для хранения "current_date",
# полученного из последнего ответа на запрос:
current_date = {'timestamp': None}


def get_homeworks(current_timestamp):
    if current_date.get('timestamp') is not None:
        # PARANOID - чтобы снизить вероятность изменения статуса домашки между
        # запросами, немного наложим интервалы времени от "from_date" до
        # момента запроса:
        payload = {'from_date': current_date.get('timestamp') - PARANOID}
    else:
        payload = {'from_date': current_timestamp}

    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}

    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL, headers=headers, params=payload
        )
    except Exception as e:
        print(f'Возникла ошибка при запросе requests: {e}')
        # tg_logger отправляет логи в Телеграм:
        logger.error(f'Возникла ошибка при запросе requests: {e}')

    homework_statuses_json = homework_statuses.json()
    current_date['timestamp'] = homework_statuses_json.get('current_date')
    return homework_statuses_json


def send_message(message):
    # tg_logger отправляет логи в Телеграм
    logger.info(f'Send_message is called. Message:\n\n{message}')
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    # словарь-кэш для хранения полученных домашек:
    current_status = {'homework': None}

    # tg_logger отправляет логи в Телеграм:
    logger.debug('Bot launched')

    while True:
        try:
            # получаем домашки за последний месяц:
            homeworks = get_homeworks(
                current_timestamp - MONTH_TIMESTAMP).get('homeworks')

            # проверяем, что полученный список домашек не None и не пустой
            # список, чтобы без ошибок получить последнюю домашку с
            # помощью индекса
            if homeworks is not None and homeworks != []:
                homework = homeworks[0]
            else:
                homework = None

            # проверяем нет ли изменений в состоянии домашки,
            # исключаем, сравнение состояний при запуске,
            # когда current_status (кэш-словарь), очевидно,
            # может отличаться от очередной запрошенной домашки:
            if (current_status.get('homework') != homework
               and current_status.get('homework') is not None):
                # tg_logger отправляет логи в Телеграм:
                logger.info('Изменение статуса домашки')
                message = parse_homework_status(homework)
                send_message(message)
                # сохраняем последнее состояние домашки, чтобы
                # сравнивать с полученной в очередном запросе домашкой:
                current_status['homework'] = homework

            time.sleep(20 * 60)  # Опрашивать раз в двадцать минут

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            logger.error(f'{e}')  # tg_logger отправляет логи в Телеграм
            time.sleep(5)


if __name__ == '__main__':
    main()
