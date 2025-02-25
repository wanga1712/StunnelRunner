import os
from loguru import logger
from secondary_functions import load_config
from database_work.check_database import check_okpd_in_db
import xml.etree.ElementTree as ET

from file_delete.file_deleter import FileDeleter
from parsing_xml.xml_parser import XMLParser


def process_okpd_files(folder_path):
    """
    Парсит все XML-файлы в указанной папке, извлекает коды ОКПД, проверяет их в базе данных
    и удаляет файл, если код не найден в базе. Пропускает обработку указанных в конфигурации папок.
    """
    okpd_data = {}

    # Загружаем конфигурацию и получаем пути папок для пропуска
    config = load_config()
    recouped_contract_archive_44_fz_xml = config.get('path', 'recouped_contract_archive_44_fz_xml', fallback=None)
    recouped_contract_archive_223_fz_xml = config.get('path', 'recouped_contract_archive_223_fz_xml', fallback=None)

    # Проверяем, является ли текущая папка одной из пропущенных
    if folder_path == recouped_contract_archive_44_fz_xml or folder_path == recouped_contract_archive_223_fz_xml:
        logger.info(f"Пропускаем папку: {folder_path}")
        return {}

    if not os.path.exists(folder_path):
        logger.error(f"Папка {folder_path} не существует.")
        return {}

    file_deleter = FileDeleter(folder_path)  # Создаем объект для удаления файлов

    logger.info(f"Начинаем парсинг XML-файлов в папке: {folder_path}")

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".xml"):
            file_path = os.path.join(folder_path, file_name)
            logger.info(f"Обрабатываем файл: {file_name}")

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    xml_content = file.read()

                # Убираем пространства имен через статический метод
                xml_content = XMLParser.remove_namespaces(xml_content)

                # Парсим XML
                root = ET.fromstring(xml_content)

                # Ищем код в первом возможном месте (тег <OKPDCode>)
                okpd_code_element = root.find(".//OKPDCode")
                if okpd_code_element is not None:
                    okpd_code = okpd_code_element.text
                    logger.debug(f"Найден код ОКПД в <OKPDCode>: {okpd_code}")
                else:
                    # Если не нашли, ищем код во втором месте (тег <code> внутри <okpd2>)
                    okpd2_code_element = root.find(".//okpd2/code")
                    if okpd2_code_element is not None:
                        okpd_code = okpd2_code_element.text
                        logger.debug(f"Найден код ОКПД в <okpd2><code>: {okpd_code}")
                    else:
                        okpd_code = None
                        logger.warning(f"Не найден код ОКПД в файле: {file_path}")

                if okpd_code:  # Если код ОКПД найден в файле
                    logger.info(f"Код ОКПД для файла {file_name}: {okpd_code}")

                    # Проверяем, если код состоит из четырех знаков и последний знак равен 0, то убираем его
                    if len(okpd_code.split('.')) == 2 and okpd_code.endswith('0'):
                        okpd_code = okpd_code[:-1]  # Удаляем последний символ (0)

                    # Проверяем наличие кода в базе данных
                    exists_in_db = check_okpd_in_db(okpd_code)  # Пытаемся найти только по sub_code

                    # Если код не найден в базе данных
                    if not exists_in_db:
                        # Удаляем файл
                        file_deleter.delete_single_file(file_path)  # Используем FileDeleter для удаления
                        logger.info(f"Файл {file_name} удалён, код ОКПД не найден в базе данных.")

                    okpd_data[file_name] = (okpd_code, exists_in_db)  # Добавляем информацию о наличии в БД
                else:
                    okpd_data[file_name] = (None, False)  # Если код не найден в файле
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {file_name}: {e}")

    logger.info(f"Завершено парсинг файлов в папке: {folder_path}")
    return okpd_data

