import os
import uuid
import requests
from urllib.parse import urlparse
from loguru import logger
from secondary_functions import load_config, load_token


class FileDownloader:
    def __init__(self, config_path="config.ini"):
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        # Загружаем токен
        self.token = load_token(self.config)
        if not self.token:
            raise ValueError("Токен не найден! Проверьте .env файл.")

        # Папка для сохранения файлов
        self.save_path = self.config.get("path", "download_dir", fallback="downloads")
        os.makedirs(self.save_path, exist_ok=True)

        logger.info(f"Файлы будут сохраняться в: {self.save_path}")

    def download_files(self, urls):
        """Скачивает файлы по переданному списку URL."""
        for url in urls:
            try:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or f"file_{uuid.uuid4().hex[:8]}.zip"
                file_path = os.path.join(self.save_path, filename)

                logger.info(f"Скачивание {url} в {file_path}...")

                headers = {'individualPerson_token': self.token}

                response = requests.get(url, stream=True, headers=headers, timeout=120)
                logger.info(f"Ответ сервера: {response.status_code} {response.reason}")

                if response.status_code == 401:
                    logger.error(f"Ошибка авторизации при скачивании {url}: {response.text}")
                    continue

                response.raise_for_status()

                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

                logger.info(f"Файл сохранен: {file_path}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при скачивании {url}: {e}")


# Тестирование
if __name__ == "__main__":
    downloader = FileDownloader(config_path="config.ini")
    test_urls = ["https://example.com/file1.zip", "https://example.com/file2.zip"]
    downloader.download_files(test_urls)
