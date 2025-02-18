import os
import uuid
import requests
from urllib.parse import urlparse
from loguru import logger
from secondary_functions import load_config, load_token

from archive_extractor import ArchiveExtractor


class FileDownloader:
    def __init__(self, config_path="config.ini"):
        """
        Инициализирует объект для скачивания файлов, загружает конфигурацию и токен.

        :param config_path: Путь к конфигурационному файлу (по умолчанию "config.ini").
        :raises ValueError: Если конфигурация или токен не могут быть загружены.
        """
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        # Загружаем токен
        self.token = load_token(self.config)
        if not self.token:
            raise ValueError("Токен не найден! Проверьте .env файл.")

        # Создаем объект для разархивации
        self.archive_extractor = ArchiveExtractor(config_path)

        # Логируем успешную загрузку конфигурации и токена
        logger.info("Конфигурация и токен загружены успешно.")

    def download_files(self, urls, document_type):
        """
        Скачивает файлы по переданному списку URL и сохраняет их в нужную папку в зависимости от типа документа.

        :param urls: Список URL для скачивания файлов.
        :param document_type: Тип документа, который используется для определения пути сохранения файлов.
        :return: Путь, куда были сохранены архивы.
        :raises: Записывает ошибки в лог при проблемах с скачиванием.
        """
        # Получаем список типов документов из конфигурации
        document_types = [doc_type.strip() for doc_type in self.config.get("eis", "documentType44_PRIZ").split(",")]

        # Определяем путь для сохранения в зависимости от типа документа
        if document_type in document_types:
            logger.info(f"Проверяемый тип документа: '{document_type}'")
            save_path = "F:\\Программирование\\Парсинг ЕИС\\44_FZ\\xml_reestr_44_fz_new_contracts"
        elif document_type in self.config.get("eis", "documentType44_RGK").split(","):
            save_path = "F:\\Программирование\\Парсинг ЕИС\\44_FZ\\xml_reestr_44_new_contracts_recouped"
        elif document_type in self.config.get("eis", "documentType223_RI223").split(","):
            save_path = "F:\\Программирование\\Парсинг ЕИС\\223_FZ\\xml_reestr_223_fz_new_contracts"
        elif document_type in self.config.get("eis", "documentType223_RD223").split(","):
            save_path = "F:\\Программирование\\Парсинг ЕИС\\223_FZ\\xml_reestr_new_223_contracts_recouped"
        else:
            logger.error(f"Не найден путь для типа документа: {document_type}")
            return None

        # Перебираем все URL в списке
        for url in urls:
            try:
                # Разбираем URL для получения имени файла
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or f"file_{uuid.uuid4().hex[:8]}.zip"
                file_path = os.path.join(save_path, filename)

                logger.info(f"Скачивание {url} в {file_path}...")

                # Устанавливаем заголовки для запроса
                headers = {'individualPerson_token': self.token}

                # Отправляем GET-запрос для скачивания файла
                response = requests.get(url, stream=True, headers=headers, timeout=120)
                response.raise_for_status()  # Проверка на успешность запроса

                # Записываем скачанный файл на диск
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

                logger.info(f"Файл сохранен: {file_path}")

                # После скачивания сразу разархивируем файл
                self.archive_extractor.unzip_files(save_path)

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при скачивании {url}: {e}")

        # Возвращаем путь, в который были сохранены архивы
        return save_path
