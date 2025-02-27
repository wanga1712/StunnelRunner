from loguru import logger
from database_work.database_connection import DatabaseManager

class DatabaseIDFetcher:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_connection(self):
        return self.db_manager.get_connection()

    def fetch_id(self, table_name, column_name, value):
        """
        Универсальный метод для получения id записи по заданному значению в указанной таблице.
        :param table_name: Название таблицы
        :param column_name: Название колонки, по которой ищем
        :param value: Значение для поиска
        :return: id записи или None, если не найдено
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            query = f"SELECT id FROM {table_name} WHERE {column_name} = %s"
            cursor.execute(query, (value,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                logger.warning(f"Запись с {column_name}={value} не найдена в {table_name}.")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении id из {table_name}: {e}")
            return None

    def get_collection_codes_okpd_id(self, code):
        return self.fetch_id("collection_codes_okpd", "code", code)

    def get_contractor_id(self, inn):
        return self.fetch_id("contractor", "inn", inn)

    def get_customer_id(self, name):
        return self.fetch_id("customer", "name", name)

    def get_dates_id(self, date_value):
        return self.fetch_id("dates", "date", date_value)

    def get_file_names_xml_id(self, file_name):
        return self.fetch_id("file_names_xml", "file_name", file_name)

    def get_key_words_names_id(self, keyword):
        return self.fetch_id("key_words_names", "keyword", keyword)

    def get_key_words_names_documentations_id(self, keyword):
        return self.fetch_id("key_words_names_documentations", "keyword", keyword)

    def get_links_documentation_223_fz_id(self, link):
        return self.fetch_id("links_documentation_223_fz", "link", link)

    def get_links_documentation_44_fz_id(self, link):
        return self.fetch_id("links_documentation_44_fz", "link", link)

    def get_okpd_from_users_id(self, code):
        return self.fetch_id("okpd_from_users", "code", code)

    def get_reestr_contract_223_fz_id(self, contract_number):
        return self.fetch_id("reestr_contract_223_fz", "contract_number", contract_number)

    def get_reestr_contract_44_fz_id(self, contract_number):
        return self.fetch_id("reestr_contract_44_fz", "contract_number", contract_number)

    def get_region_id(self, name):
        return self.fetch_id("region", "name", name)

    def get_stop_words_names_id(self, word):
        return self.fetch_id("stop_words_names", "word", word)

    def get_trading_platform_id(self, name):
        return self.fetch_id("trading_platform", "name", name)

    def get_users_id(self, username):
        return self.fetch_id("users", "username", username)

    def close(self):
        self.db_manager.close()
