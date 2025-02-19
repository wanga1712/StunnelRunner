from database_work.database_connection import DatabaseManager
from loguru import logger


def get_region_codes():
    """
    Получает список всех кодов регионов из базы данных.

    :return: Список кодов регионов (list[str])
    """
    db = DatabaseManager()

    try:
        query = "SELECT code FROM region ORDER BY code;"
        db.cursor.execute(query)
        codes = [row[0] for row in db.cursor.fetchall()]
        logger.debug(f"Получены коды регионов: {codes}")
        return codes
    except Exception as e:
        logger.exception(f"Ошибка при получении кодов регионов: {e}")
        return []
    finally:
        db.cursor.close()
        db.connection.close()