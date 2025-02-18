import os
import zipfile
from loguru import logger
from secondary_functions import load_config


class ArchiveExtractor:
    def __init__(self, config_path="config.ini"):
        """
        Инициализирует объект ArchiveExtractor, загружая настройки из конфигурационного файла.

        :param config_path: Путь к конфигурационному файлу (по умолчанию "config.ini").
        :raises ValueError: Если не удалось загрузить конфигурацию.
        """
        # Загружаем настройки из конфигурационного файла
        self.config = load_config(config_path)
        if not self.config:
            # Если конфигурация не была загружена, выбрасываем исключение
            raise ValueError("Ошибка загрузки конфигурации!")

    def unzip_files(self, directory):
        """
        Разархивирует все ZIP-файлы в указанной директории.

        :param directory: Путь к директории, в которой находятся ZIP-файлы.
        :raises Exception: Если произошла ошибка при разархивировании файла.
        """
        # Логируем путь для разархивирования
        logger.info(f"Путь для разархивирования: {directory}")

        # Перебираем все файлы в указанной директории
        for file_name in os.listdir(directory):
            # Если файл является ZIP-архивом
            if file_name.endswith('.zip'):
                zip_path = os.path.join(directory, file_name)
                try:
                    # Логируем начало разархивирования
                    logger.info(f"Разархивирование {zip_path}...")
                    # Открываем ZIP-архив для чтения
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Извлекаем все файлы в указанную директорию
                        zip_ref.extractall(directory)
                    # Логируем успешное завершение разархивирования
                    logger.info(f"Разархивирование завершено для {zip_path}.")
                except zipfile.BadZipFile:
                    # Логируем ошибку, если файл не является корректным ZIP-архивом
                    logger.error(f"Не удалось разархивировать файл: {zip_path}")
                except Exception as e:
                    # Логируем любые другие ошибки при разархивировании
                    logger.error(f"Ошибка при разархивировании файла {zip_path}: {e}")
