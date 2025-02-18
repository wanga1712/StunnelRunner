import os
import zipfile
from loguru import logger
from secondary_functions import load_config


class ArchiveExtractor:
    def __init__(self, config_path="config.ini"):
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

    def unzip_files(self, directory):
        """Разархивирует файлы в указанной директории."""
        logger.info(f"Путь для разархивирования: {directory}")
        for file_name in os.listdir(directory):
            if file_name.endswith('.zip'):
                zip_path = os.path.join(directory, file_name)
                try:
                    logger.info(f"Разархивирование {zip_path}...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(directory)
                    logger.info(f"Разархивирование завершено для {zip_path}.")
                except zipfile.BadZipFile:
                    logger.error(f"Не удалось разархивировать файл: {zip_path}")
                except Exception as e:
                    logger.error(f"Ошибка при разархивировании файла {zip_path}: {e}")

