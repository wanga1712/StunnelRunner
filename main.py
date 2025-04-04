import os
import time
import json
import configparser
from datetime import datetime, timedelta
from loguru import logger
from stunnel_runner import StunnelRunner
from eis_requester import EISRequester

# Пути к файлам
CONFIG_PATH = "config.ini"
PROCESSED_DATES_FILE = "processed_dates.json"

START_DATE = datetime(2024, 1, 11)  # Начальная дата
TODAY = datetime.today()  # Текущая дата

# Настройка логирования в одном месте
logger.add("errors.log", level="ERROR", rotation="1 week", compression="zip")

def load_processed_dates():
    """Загружает список уже обработанных дат из JSON-файла."""
    if os.path.exists(PROCESSED_DATES_FILE):
        with open(PROCESSED_DATES_FILE, "r") as file:
            return set(json.load(file))  # Храним даты в виде множества
    return set()

def save_processed_date(date_str):
    """Сохраняет отработанную дату в JSON-файл."""
    processed_dates = load_processed_dates()
    processed_dates.add(date_str)

    with open(PROCESSED_DATES_FILE, "w") as file:
        json.dump(list(processed_dates), file, indent=4)

def get_current_date():
    """Читает текущую дату из config.ini, исправлена проблема с кодировкой."""
    config = configparser.ConfigParser()
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config.read_file(file)  # Читаем файл с явной кодировкой UTF-8

    return datetime.strptime(config.get("eis", "date", fallback=START_DATE.strftime("%Y-%m-%d")), "%Y-%m-%d")


def update_config_date(new_date):
    """Обновляет дату в config.ini с явной кодировкой UTF-8."""
    config = configparser.ConfigParser()

    # Читаем файл с правильной кодировкой
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config.read_file(file)

    config.set("eis", "date", new_date.strftime("%Y-%m-%d"))

    # Записываем обратно в файл с нужной кодировкой
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        config.write(config_file)

    logger.info(f"Дата в config.ini обновлена: {new_date.strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    logger.info("Запуск программы...")

    # Запуск Stunnel
    stunnel_runner = StunnelRunner()
    stunnel_runner.run_stunnel()
    logger.info("Stunnel успешно запущен.")

    processed_dates = load_processed_dates()

    # Читаем начальную дату из конфигурации
    current_date = get_current_date()

    while current_date <= TODAY:
        date_str = current_date.strftime("%Y-%m-%d")

        # Пропускаем дату, если она уже была обработана
        if date_str in processed_dates:
            logger.info(f"Дата {date_str} уже обработана, пропускаем...")
        else:
            logger.info(f"Обработка данных за {date_str}...")
            eis_requester = EISRequester()
            eis_requester.process_requests()

            # # Сохраняем отработанную дату
            # save_processed_date(date_str)

        # Обновляем дату на следующий день
        next_date = current_date + timedelta(days=1)
        update_config_date(next_date)

        # Опционально: можно добавить небольшую задержку
        time.sleep(2)

        # Переходим к следующему дню
        current_date = next_date

    logger.info("Программа завершена.")
