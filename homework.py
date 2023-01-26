import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exeption import APIError

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename="main.log",
    filemode="w",
    format="%(asctime)s, %(levelname)s, %(funcName)s, %(message)s",
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
    env = {
        "PRACTICUM_TOKEN": PRACTICUM_TOKEN,
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    logger = logging.getLogger(__name__)
    for env_elem in env:
        if env[env_elem] is None or env[env_elem] == "":
            logger.critical('"{}" is None'.format(env_elem))
            return False
    logger.debug("Environment filled in successfull!")
    return True


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
    logger = logging.getLogger(__name__)
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
    except requests.RequestException as error:
        logger, error(error)
        raise error

    if response.status_code is not HTTPStatus.OK:
        logger.error(
            f"Request to '{ENDPOINT}'"
            f"finised with {response.status_code}"
        )
        raise APIError(f"Status code of requests {response.status_code}")
    try:
        return response.json()
    except Exception as error:
        logging.error(error)
        raise error


def check_response(response):
    """Проверяет наличие необходимых ключей в ответе от API."""
    logger = logging.getLogger(__name__)
    if not isinstance(response, dict):
        logger.debug("Expected dictionary from API")
        raise TypeError("Ожидался словарь от API")
    if ("homeworks" not in response) or "current_date" not in response:
        logger.debug(
            "Expected dictionary with key 'homework' and 'current_date'")
        raise TypeError("В ответе нет ключа 'homework' или 'current_date'")
    homeworks = response["homeworks"]
    if not isinstance(homeworks, list):
        logger.debug("Expected list in key 'homework'")
        raise TypeError("В ответе нет ключа 'homework' или 'current_date'")
    return homeworks


def parse_status(homework):
    """Возвращает статус работы."""
    logger = logging.getLogger(__name__)
    homework_name = homework.get("homework_name")
    if homework_name is None:
        logger.debug("'homework' dose not have key 'homework_name'")
        raise TypeError("В словаре 'homework' ожидался ключ 'homework_name'")

    status = homework.get("status")
    if status is None:
        logger.debug("'homework' dose not have key 'status'")
        raise TypeError("В словаре 'homework' ожидался ключ 'status'")

    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict is None:
        logger.debug("'HOMEWORK_VERDICTS' dose not have key 'status'")
        raise TypeError("Неизвестный статус работы")

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    answers = {}

    while True:
        try:
            response = get_api_answer(timestamp=timestamp)
            homeworks = check_response(response)

            homeworks = response["homeworks"]
            for homework in homeworks:
                message = parse_status(homework)

                homework_name = homework["homework_name"]
                status = homework["status"]

                if homework_name in answers:
                    if status != answers[homework_name]:
                        send_message(bot, message)
                        answers[homework_name] = status
                else:
                    answers[homework_name] = status
                    send_message(bot, message)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(error)
            send_message(bot, message=message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
