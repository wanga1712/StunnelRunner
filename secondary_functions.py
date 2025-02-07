import json
import configparser
from loguru import logger

# Загружаем конфигурацию с обработкой ошибок
config = configparser.ConfigParser()
try:
    config.read("config.ini", encoding="utf-8")
    regions_file = config.get("system", "regions_file")
    logger.info(f"Файл конфигурации загружен успешно. regions_file: {regions_file}")
except configparser.DuplicateOptionError as e:
    logger.error(f"Ошибка: Дублирование ключей в config.ini: {e}")
    raise
except Exception as e:
    logger.error(f"Ошибка загрузки config.ini: {e}")
    raise

# Функция для загрузки данных о регионах из JSON файла
def load_regions():
    """Загружает словарь регионов из JSON-файла."""
    try:
        with open(regions_file, "r", encoding="utf-8") as file:
            regions = json.load(file)
            logger.info(f"Файл регионов {regions_file} успешно загружен. Найдено регионов: {len(regions)}")
            return regions
    except FileNotFoundError:
        logger.error(f"Ошибка: Файл {regions_file} не найден!")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка в файле {regions_file}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Неизвестная ошибка при загрузке регионов: {e}")
        return {}

# Функция для получения списка кодов регионов
def get_region_codes():
    """Возвращает список всех кодов регионов."""
    regions = load_regions()
    if not regions:
        logger.warning("Словарь регионов пуст. Проверьте файл JSON!")
    return [int(code) for code in regions.keys()]  # Преобразуем ключи в числа

# Отладочный запуск
if __name__ == "__main__":
    logger.debug("Запуск тестового выполнения get_region_codes()")
    region_codes = get_region_codes()
    logger.debug(f"Получены коды регионов: {region_codes}")
