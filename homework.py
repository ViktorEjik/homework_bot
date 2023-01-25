import json
import logging
import os
import sys
import time
from pprint import pprint

import requests
import telegram
from dotenv import load_dotenv

from exeption import APIError, EnvironmentError, IncorrectKey

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename="main.log",
    filemode="w",
    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s",
)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens():
    """Проверка на валидность переменных окружения."""
    try:
        if PRACTICUM_TOKEN is None:
            raise EnvironmentError(
                "The variable environment is not complete!"
                " Fill in PRACTICUM_TOKEN"
            )
        if TELEGRAM_TOKEN is None:
            raise EnvironmentError(
                "The variable environment is not complete!"
                " Fill in TELEGRAM_TOKEN"
            )
        if TELEGRAM_CHAT_ID is None:
            raise EnvironmentError(
                "The variable environment is not complete!"
                " Fill in TELEGRAM_CHAT_ID"
            )
    except EnvironmentError as error:
        logging.critical(error)
        sys.exit()
    else:
        logging.debug("Environment filled in successfull!")


def send_message(bot, message):
    """Отсылает сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f"Error sending message {error}")
        raise Exception(f"Error sending message {error}")
    else:
        logging.debug("Message was sent successfully!")


def get_api_answer(timestamp):
    """Обращается к API и преобразует отвек к dict."""
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={"from_date": timestamp}
        )
    except requests.RequestException as error:
        logging, error(error)
        raise error
    if 400 <= response.status_code <= 500:
        error = APIError(f"Status code of requests {response.status_code}")
        logging.error(error)
        raise error
    try:
        return response.json()
    except json.decoder.JSONDecodeError:
        error = APIError('Response dose not have "json"')
        logging.error(error)
        raise error
    except Exception as error:
        logging.error(error)
        raise error


def check_response(response):
    """Проверяет наличие необходимых ключей в ответе от API."""
    if type(response) is not dict:
        logging.debug("Expected dictionary from API")
        raise TypeError("Ожидался словарь от API")
    try:
        homeworks = response["homeworks"]
        if type(homeworks) is not list:
            logging.debug('Expected list in key "homeworks"')
            raise TypeError('Ожидался список по ключу "homeworks"')
    except KeyError as error:
        logging.error(error)
        raise TypeError("Не сущестует ключа homeworks")
    else:
        return homeworks


def parse_status(homework):
    """Возвращает статус работы."""
    try:
        homework_name = homework["homework_name"]
    except KeyError as error:
        logging.error(error)
        raise TypeError("Не существует ключа homework_name")

    try:
        status = homework["status"]
    except KeyError as error:
        logging.error(error)
        raise TypeError("Не существует ключа status")

    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as error:
        logging.error(error)
        raise IncorrectKey(f"Ключа {status} не существует")

    except Exception as error:
        logging.error(error)
        raise IncorrectKey(f"Неизвестная ошибка для ключа {status}")

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    ansvers = {}

    while True:
        try:
            response = get_api_answer(timestamp=timestamp)
            homeworks = check_response(response)

            homeworks = response["homeworks"]
            for homework in homeworks:
                message = parse_status(homework)

                homework_name = homework["homework_name"]
                status = homework["status"]

                if homework_name in ansvers:
                    if status != ansvers[homework_name]:
                        send_message(bot, message)
                        ansvers[homework_name] = status
                else:
                    ansvers[homework_name] = status
                    send_message(bot, message)
            pprint(ansvers)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(error)
            send_message(bot, message=message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
