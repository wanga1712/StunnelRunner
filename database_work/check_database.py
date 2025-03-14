from loguru import logger

from file_delete.file_deleter import FileDeleter
from database_work.database_connection import DatabaseManager
from database_work.database_id_fetcher import DatabaseIDFetcher


class DatabaseCheckManager:
    """
    Класс для управления проверкой и взаимодействием с базой данных.

    Этот класс включает методы для:
    - Проверки существования ОКПД в базе данных.
    - Проверки, записано ли имя файла в таблице `file_names_xml`.
    - Проверки ИНН заказчика и получения его ID из базы данных.
    """

    def __init__(self):
        """
        Инициализирует экземпляры классов для работы с базой данных.

        Использует `DatabaseManager` для взаимодействия с базой данных и
        `DatabaseIDFetcher` для получения ID заказчика.
        """
        logger.add("errors.log", level="ERROR", rotation="10 MB", compression="zip")

        self.db_manager = DatabaseManager()
        self.id_fetcher = DatabaseIDFetcher()

    def get_db_manager(self):
        """
        Возвращает экземпляр `DatabaseManager`.

        :return: Экземпляр класса `DatabaseManager`
        """
        return self.db_manager

    def close(self):
        """
        Закрывает соединение с базой данных.

        :return: None
        """
        self.db_manager.close()

    def check_okpd_in_db(self, okpd_code_sub):
        """
        Проверяет, существует ли код ОКПД в базе данных.

        :param okpd_code_sub: Код ОКПД (sub_code), который необходимо проверить.
        :return: True, если код найден в базе данных, иначе False.
        """
        try:
            query = """
            SELECT EXISTS(
                SELECT 1 
                FROM collection_codes_okpd 
                WHERE sub_code = %s
            );
            """
            result = self.db_manager.fetch_one(query, (okpd_code_sub,))
            return bool(result)  # Приведение к bool на случай None
        except Exception as e:
            logger.exception(f"Ошибка при проверке ОКПД: {e}")
            return False

    # Удалить за ненадобностью после проверки
    # def check_inn_and_get_id_customer(self, inn):
    #     """
    #     Проверяет, существует ли ИНН в таблице `customer` и возвращает ID.
    #
    #     :param inn: ИНН заказчика, который необходимо проверить.
    #     :return: ID заказчика, если ИНН найден в базе данных, иначе None.
    #     """
    #     customer_id = self.id_fetcher.get_customer_id(inn)
    #
    #     if customer_id:
    #         logger.info(f"ИНН {inn} найден в базе данных, id: {customer_id}")
    #         return customer_id  # Возвращаем ID заказчика, если он найден
    #
    #     logger.warning(f"ИНН {inn} не найден в базе данных.")
    #     return None  # Если ИНН не найден, просто возвращаем None, без попытки обновить базу
