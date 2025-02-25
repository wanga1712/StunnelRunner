from loguru import logger
from database_work.database_connection import DatabaseManager

class DatabaseChecks:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def is_download_date_recorded(self, download_date: str) -> bool:
        """
        Проверяет, записана ли уже указанная дата скачивания в БД.

        :param download_date: Дата скачивания в формате YYYY-MM-DD
        :return: True, если дата уже есть в БД, иначе False
        """
        query = "SELECT EXISTS(SELECT 1 FROM downloads WHERE download_date = %s);"
        result = self.db_manager.fetch_one(query, (download_date,))
        exists = result[0] if result else False
        logger.info(f"Проверка даты {download_date} в БД: {'найдена' if exists else 'не найдена'}")
        return exists

    def is_file_name_recorded(self, file_name: str) -> bool:
        """
        Проверяет, записано ли уже указанное имя файла в таблице file_names_xml.

        :param file_name: Название файла
        :return: True, если файл уже есть в БД, иначе False
        """
        query = "SELECT EXISTS(SELECT 1 FROM file_names_xml WHERE file_name = %s);"
        result = self.db_manager.fetch_one(query, (file_name,))
        exists = result[0] if result else False
        logger.info(f"Проверка имени файла {file_name} в БД: {'найден' if exists else 'не найден'}")
        return exists
