import logging
import os
import time

import requests
import telegram
import tg_logger
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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

tg_logger.setup(logger, token=TELEGRAM_TOKEN, users=[CHAT_ID])

# проинициализируйте бота здесь,
# чтобы он был доступен в каждом нижеобъявленном методе,
# и не нужно было прокидывать его в каждый вызов
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    homework_statuses = requests.get(url, headers=headers, params=payload)
    return homework_statuses.json()


def send_message(message):
    logger.info('send_message is called')
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    current_status = {'homework': None}
    logger.debug('Bot launched')
    while True:
        try:
            # получаем домашки за последний месяц
            homeworks = get_homeworks(current_timestamp - 2629743)
            homework = homeworks['homeworks'][0]  # извлекаем последнюю домашку
            # проверяем нет ли изменений в состоянии домашки,
            # исключаем, сравнение состояний при первом запуске,
            # когда current_status, очевидно, отличается от очередной
            # запрошенной домашки:
            if (current_status['homework'] != homework
               and current_status['homework'] is not None):
                logger.info('Изменение статуса домашки')
                message = parse_homework_status(homework)
                send_message(message)
                # созраняем последнее состояние домашки, чтобы
                # сравнивать с полученной в очередном запросе домашкой:
                current_status['homework'] = homework
            time.sleep(20 * 60)  # Опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            logger.error(f'{e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
