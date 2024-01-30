import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверка наличия переменных окружения."""
    if all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        logger.critical('Отсутствуют обязательные переменные окружения')
        return False


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug('Сообщение успешно отправлено')
    except exceptions.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    timestamp = timestamp or int(time.time())
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=payload)
        if homework_statuses.status_code != HTTPStatus.OK:
            logger.error(f'Ошибка запроса к API:'
                         f'{homework_statuses.status_code}')
            raise ValueError('Ошибка запроса к API')
        return homework_statuses.json()
    except requests.RequestException as error:
        logger.error(f'Ошибка запроса к API: {error}')
        raise exceptions.InvalidRequestResponse('Ошибка запроса к API')
    except Exception as e:
        logger.error(f'Ошибка запроса к API: {e}')
        raise exceptions.InvalidRequestResponse('Ошибка запроса к API')


def check_response(response):
    """Проверка ответа от API на корректность."""
    logger.debug('Проверка ответа API')
    if not isinstance(response, dict):
        raise TypeError(f'Ожидал в ответе API - dict, '
                        f'а получил - {type(response)}')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response:
        raise exceptions.HomeworkEmptyException(
            'Не получил homeworks в ответе API')
    if not isinstance(homeworks, list):
        raise TypeError(f'Ожидал получить homeworks в формате - list, '
                        f'а получил {type(homeworks)}')
    return homeworks


def parse_status(homework):
    """Парсинг статуса работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе нету ключа homework_name')
    if 'status' not in homework:
        raise KeyError('В ответе нету ключа status')
    homework_name = homework.get('homework_name')
    homework_verdict = homework.get('status')
    if homework_verdict not in HOMEWORK_VERDICTS:
        raise ValueError(f'Выдан неизвестный статус работы - '
                         f'{homework_verdict}')
    verdict = HOMEWORK_VERDICTS[homework_verdict]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Нету обязательных переменных окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    old_status = new_status = ''
    logger.debug('Запуск работы бота')
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            new_homeworks = check_response(response)
            if new_homeworks:
                homework = new_homeworks[0]
                new_status = homework.get('status')
            else:
                old_status = 'empty'
            if new_status != old_status:
                message = parse_status(homework)
                send_message(bot, message)
                old_status = new_status
            else:
                logger.debug('Нету новых домашек')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            new_status = message
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        format='%(asctime)s - %(levelname)s - %(message)s - %(name)s'
    )
    logger.addHandler(
        logging.StreamHandler()
    )

    main()
