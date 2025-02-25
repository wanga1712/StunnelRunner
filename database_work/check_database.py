from loguru import logger
from database_work.database_connection import DatabaseManager

def check_okpd_in_db(okpd_code_sub):
    """
    Проверяет, существует ли код ОКПД в базе данных по sub_code.

    :param okpd_code_sub: Код ОКПД (sub_code)
    :return: True, если код найден в базе данных, иначе False
    """
    # Создаем объект для работы с базой данных
    db_manager = DatabaseManager()

    try:
        # Выполняем запрос на проверку наличия только sub_code в базе данных
        query = """
        SELECT EXISTS(
            SELECT 1 
            FROM collection_codes_okpd 
            WHERE sub_code = %s
        );
        """
        # Параметры для проверки: ищем только по sub_code
        result = db_manager.fetch_one(query, (okpd_code_sub,))
        # Возвращаем результат
        return result[0]  # Если результат 1, то код существует, иначе False
    except Exception as e:
        logger.exception(f"Ошибка при проверке ОКПД: {e}")
        return False
    finally:
        db_manager.close()  # Закрываем соединение с базой данных
