import json
import configparser
import os
from dotenv import load_dotenv
from loguru import logger


def load_config(config_path="config.ini"):
    """Загружает конфигурационный файл и возвращает объект ConfigParser"""
    config = configparser.ConfigParser()
    try:
        config.read(config_path, encoding="utf-8")
        return config
    except configparser.Error as e:
        logger.error(f"Ошибка загрузки config.ini: {e}")
        raise


def check_file_exists(file_path, description):
    """Проверяет существование файла и логирует ошибку, если его нет"""
    if not os.path.exists(file_path):
        logger.error(f"Файл {description} не найден: {file_path}")
        return False
    return True


def load_regions(regions_file):
    """Загружает словарь регионов из JSON-файла"""
    if not check_file_exists(regions_file, "регионов"):
        return {}

    try:
        with open(regions_file, "r", encoding="utf-8") as file:
            regions = json.load(file)
            logger.info(f"Загружено {len(regions)} регионов из {regions_file}")
            return regions
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка в JSON-файле {regions_file}: {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при загрузке регионов: {e}")

    return {}


def get_region_codes(regions_file):
    """Возвращает список кодов регионов"""
    regions = load_regions(regions_file)
    return [int(code) for code in regions.keys()] if regions else []


def load_token(config):
    """Загружает токен из .env файла, путь к которому хранится в config.ini"""
    env_path = config.get("path", "env_file", fallback=None)

    if not env_path:
        logger.error("Путь к .env файлу не найден в config.ini")
        return None

    env_path = os.path.normpath(env_path)  # Приводим путь к корректному формату

    if not check_file_exists(env_path, ".env"):
        return None

    load_dotenv(env_path)  # Загружаем .env файл
    token = os.getenv("TOKEN")

    if token:
        logger.info("Токен загружен успешно.")
    else:
        logger.error("Токен не найден в .env файле.")

    return token


# --- Основной блок кода ---
if __name__ == "__main__":
    config = load_config()

    # Загружаем путь к файлу регионов
    regions_file = config.get("path", "regions_file", fallback=None)
    if not regions_file:
        logger.error("Путь к файлу регионов не указан в config.ini")
    else:
        logger.info(f"Файл регионов: {regions_file}")

    token = load_token(config)

    logger.debug("Программа завершила работу.")
