import logging
import os
import time
import requests
import telegram
from dotenv import load_dotenv
# from logging import FileHandler, StreamHandler
import json

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log', 
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('my_logger.log')
stream_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# проинициализируйте бота здесь,
# чтобы он был доступен в каждом нижеобъявленном методе,
# и не нужно было прокидывать его в каждый вызов
bot = telegram.Bot(token=TELEGRAM_TOKEN)  # !


def parse_homework_status(homework):
    homework_name = homework['homework_name']  # !
    if homework['status'] == 'rejected':  # !
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'  # !
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}  # !
    payload = {'from_date': current_timestamp}  # !
    homework_statuses = requests.get(url, headers=headers, params=payload)  # !
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    current_status = {'homework': None}
    while True:
        try:
            homeworks = get_homeworks(current_timestamp - 2629743)  # !
            homework = homeworks['homeworks'][0]  # !
            if (current_status['homework'] != homework
               and current_status['homework'] != None):
                message = parse_homework_status(homework)  # !
                send_message(message)  # !
                current_status['homework'] = homework

            # homework = json.dumps(homeworks)
            # send_message(homework)
            time.sleep(5 * 60)  # Опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
