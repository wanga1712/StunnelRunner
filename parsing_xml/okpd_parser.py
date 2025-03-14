import os
from loguru import logger
import xml.etree.ElementTree as ET
import time

from secondary_functions import load_config
from database_work.check_database import DatabaseCheckManager
from database_work.database_id_fetcher import DatabaseIDFetcher
from file_delete.file_deleter import FileDeleter
from parsing_xml.xml_parser import XMLParser   # Импортируем функцию process_file из xml_parser.py


logger.add("errors.log", level="ERROR", rotation="10 MB", compression="zip")

def process_okpd_files(folder_path, region_code):
    """
    Парсит все XML-файлы в указанной папке, извлекает коды ОКПД, проверяет их в базе данных
    и удаляет файл, если код не найден в базе. Пропускает обработку указанных в конфигурации папок.
    :param folder_path: Путь к папке с распакованными файлами
    :param region_code: Код региона из SOAP-запроса
    """
    db_id_fetcher = DatabaseIDFetcher()  # Инициализируем объект для получения ID
    region_id = db_id_fetcher.get_region_id(region_code)  # Получаем ID региона

    if not region_id:
        logger.error(f"Не удалось получить ID региона для кода {region_code}")
        return

    # Загружаем конфигурацию и получаем пути папок для пропуска
    config = load_config()
    recouped_contract_archive_44_fz_xml = config.get('path', 'recouped_contract_archive_44_fz_xml', fallback=None)
    recouped_contract_archive_223_fz_xml = config.get('path', 'recouped_contract_archive_223_fz_xml', fallback=None)

    if folder_path in [recouped_contract_archive_44_fz_xml, recouped_contract_archive_223_fz_xml]:
        logger.info(f"Пропускаем папку: {folder_path}")
        return

    if not os.path.exists(folder_path):
        logger.error(f"Папка {folder_path} не существует.")
        return

    file_deleter = FileDeleter(folder_path)
    db_manager = DatabaseCheckManager()

    logger.info(f"Начинаем парсинг XML-файлов в папке: {folder_path}")

    for file_name in os.listdir(folder_path):
        if not file_name.endswith(".xml"):
            continue

        file_path = os.path.join(folder_path, file_name)
        logger.info(f"Обрабатываем файл: {file_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                xml_content = file.read()

            xml_content = XMLParser.remove_namespaces(xml_content)
            root = ET.fromstring(xml_content)

            okpd_code = None
            okpd_code_element = root.find(".//OKPDCode")
            if okpd_code_element is not None:
                okpd_code = okpd_code_element.text
                logger.debug(f"Найден код ОКПД в <OKPDCode>: {okpd_code}")
            else:
                okpd2_code_element = root.find(".//okpd2/code")
                if okpd2_code_element is not None:
                    okpd_code = okpd2_code_element.text
                    logger.debug(f"Найден код ОКПД в <okpd2><code>: {okpd_code}")

            if okpd_code:
                logger.debug(f"Обработанный код ОКПД для файла {file_name}: {okpd_code}")

                # Проверяем, если код состоит из 2-х частей и заканчивается на '0'
                if len(okpd_code.split('.')) == 2 and okpd_code.endswith('0'):
                    okpd_code = okpd_code[:-1]  # Убираем последний '0'
                    logger.debug(f"Код ОКПД после изменения: {okpd_code}")

                # Если код состоит из большего количества частей, например, 21.11.00.25
                elif len(okpd_code.split('.')) > 2:
                    logger.debug(f"Код ОКПД {okpd_code} имеет больше частей.")

                    exists_in_db = db_manager.check_okpd_in_db(okpd_code)
                    if exists_in_db:
                        logger.info(f"Код ОКПД {okpd_code} найден в базе данных.")

                        # Проверяем, если файл уже есть в БД, удаляем его и переходим к следующему файлу
                        file_id = db_id_fetcher.get_file_names_xml_id(file_name)

                        if file_id:  # Если файл уже есть в БД
                            logger.info(f"Файл {file_name} уже был записан в БД. Завершаем обработку.")
                            file_deleter.delete_single_file(file_path)
                            continue  # Переходим к следующему файлу
                        else:
                            # Если файла нет в БД, выполняем дальнейшую обработку
                            logger.info(f"Файл {file_name} не найден в базе данных, выполняем дальнейшую обработку.")
                            xml_parser = XMLParser(config_path="config.ini")
                            xml_parser.parse_xml_tags(os.path.dirname(file_path), region_code, okpd_code)

                            # Задержка перед удалением файла, чтобы дать время на запись в БД
                            time.sleep(1)  # 1 секунда задержки (можно настроить по необходимости)

                            # Удаляем файл после обработки
                            file_deleter.delete_single_file(file_path)
                            # logger.error(f'файл {file_path} удален')
                    else:
                        logger.info(f"Код ОКПД {okpd_code} не найден в базе данных, файл будет удален.")
                        file_deleter.delete_single_file(file_path)
                        continue  # Прекращаем обработку файла, если код не найден в базе

            else:
                logger.warning(f"Не найден код ОКПД в файле {file_name}")
                file_deleter.delete_single_file(file_path)

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_name}: {e}")

    logger.info(f"Завершено парсинг файлов в папке: {folder_path}")
