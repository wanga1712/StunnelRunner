import os
import json
import xml.etree.ElementTree as ET
from loguru import logger
import re

from secondary_functions import load_config
from database_work.check_database import DatabaseCheckManager
from database_work.database_operations import DatabaseOperations
from database_work.database_id_fetcher import DatabaseIDFetcher


class XMLParser:
    """
    Класс для обработки XML-файлов в указанной директории.
    """

    def __init__(self, config_path="config.ini"):
        """
        Загружает конфигурацию и путь к XML-файлам из config.ini.
        """

        logger.add("errors.log", level="ERROR", rotation="10 MB", compression="zip")

        # Инициализируем методы для работы с базой данных внутри XMLParser
        self.database_check_manager = DatabaseCheckManager()
        self.database_operations = DatabaseOperations()
        self.db_id_fetcher = DatabaseIDFetcher()

        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        # Пути к папкам с XML и теги для каждой папки из конфигурации
        self.xml_paths = self.config['path']
        self.tags_paths = self.config['tags']

    @staticmethod
    def remove_namespaces(xml_string):
        """
        Полностью удаляет все пространства имен из XML-строки.
        Убирает как префиксы, так и их определения.
        """
        # Удаление всех атрибутов xmlns:... и xmlns="..."
        no_namespaces = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', xml_string)

        # Удаление всех префиксов вида <ns3:tag> и </ns3:tag>
        no_namespaces = re.sub(r'<(/?)(\w+):', r'<\1', no_namespaces)

        # Также важно удалить префикс внутри атрибутов, если он есть (например, ns5:href)
        no_namespaces = re.sub(r'(\s)(\w+):', r'\1', no_namespaces)

        return no_namespaces

    def load_json_tags(self, tags_path):
        """
        Загружает теги из указанного JSON файла.
        """
        try:
            with open(tags_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при загрузке JSON файла с тегами {tags_path}: {e}")
            return None

    def parse_reestr_contract(self, root, tags, region_code, okpd_code, customer_id, platform_id, tags_file):
        """
        Парсит данные для таблицы реестра контрактов и вставляет в БД.
        Также добавляет customer_id и platform_id.
        """

        found_tags = {}

        for tag, xpath in tags.items():
            # Убираем пространство имен из пути
            tag_without_namespace = xpath.split(":")[-1]

            # Ищем тег на любом уровне
            elements = root.findall(f".//{tag_without_namespace}")

            if elements:
                values = [elem.text.strip() for elem in elements if elem.text and elem.text.strip()]
                found_tags[tag] = values[0] if values else None

                # if values:
                # logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
            else:
                found_tags[tag] = None

        # Добавляем дополнительные параметры
        found_tags['region_id'] = self.db_id_fetcher.get_region_id(region_code)
        found_tags['okpd_id'] = self.db_id_fetcher.get_okpd_id(okpd_code)
        found_tags['customer_id'] = customer_id
        found_tags['trading_platform_id'] = platform_id

        # Выбираем правильную функцию вставки в БД
        if tags_file == self.tags_paths['get_tags_44_new']:
            contract_id = self.database_operations.insert_reestr_contract_44_fz(found_tags)
        elif tags_file == self.tags_paths['get_tags_223_new']:
            contract_id = self.database_operations.insert_reestr_contract_223_fz(found_tags)
        else:
            logger.error(f"Неизвестный файл тегов: {tags_file}")
            return None

        logger.info(f"Вставленная запись имеет id: {contract_id}")

        return contract_id

    def parse_trading_platform(self, root, tags):
        """
        Парсит данные для таблицы trading_platform, проверяя наличие записи.
        Если запись уже есть, просто возвращает ее ID, иначе создает новую запись.
        """
        found_tags = {}

        # Парсим данные из XML
        for tag, xpath in tags.items():
            element = root.find(f".//{xpath}")  # Добавляем ".//" для поиска на любом уровне
            found_tags[tag] = element.text.strip() if element is not None and element.text else None

        # Если нет имени площадки — не можем работать дальше
        trading_platform_name = found_tags.get('trading_platform_name')
        if not trading_platform_name:
            logger.error("Не удалось найти имя торговой площадки.")
            return None

        # Получаем ID площадки по имени
        platform_id = self.db_id_fetcher.get_trading_platform_id(trading_platform_name)

        if platform_id:
            logger.info(f"Торговая площадка '{trading_platform_name}' уже существует, ID: {platform_id}")
            return platform_id  # Если нашли, просто возвращаем ID

        # Если площадки нет в БД, проверяем наличие URL перед вставкой
        if found_tags.get('trading_platform_url'):
            platform_id = self.database_operations.insert_trading_platform(found_tags)
            if platform_id:
                logger.info(f"Добавлена новая торговая площадка с ID: {platform_id}")
            else:
                logger.error(f"Не удалось добавить торговую площадку '{trading_platform_name}' в БД.")
        else:
            logger.warning(f"Не удалось найти URL для торговой площадки '{trading_platform_name}', запись не создана.")

        return platform_id  # Возвращаем либо найденный, либо вновь созданный ID

    def parse_customer(self, root, tags, tags_file):
        """
        Парсит данные для таблицы customer, проверяя наличие ИНН в базе данных.
        Если ИНН существует, обновляет данные, если нет — добавляет нового заказчика.
        """
        found_tags = {}

        for tag, xpath in tags.items():
            element = root.find(f".//{xpath}")

            if element is None or element.text is None:
                found_tags[tag] = None
                continue

            if tags_file == self.tags_paths['get_tags_44_new']:
                # Логируем перед вызовом strip(), чтобы понять, что там лежит
                try:
                    found_tags[tag] = element.text.strip()
                except AttributeError:
                    logger.error(f"Ошибка при обработке тега '{tag}': element.text = {element.text}")
                    found_tags[tag] = None  # Чтобы не упасть дальше, если будет ошибка
                else:
                    logger.info(f"Тег '{tag}' успешно обработан: {found_tags[tag]}")

            elif tags_file == self.tags_paths['get_tags_223_new']:
                # В 223-ФЗ длинные текстовые блоки, их оставляем как есть
                found_tags[tag] = element.text

            else:
                logger.error(f"Неизвестный файл тегов: {tags_file}")
                return None

        # Проверяем наличие ИНН
        inn = found_tags.get('customer_inn')
        customer_id = None

        if inn:
            customer_data = found_tags
            customer_id = self.db_id_fetcher.get_customer_id(inn)

            if customer_id:
                logger.info(f"Обновляем данные заказчика с ID {customer_id}")
                self.database_operations.update_customer(customer_data, customer_id, tags_file)
            else:
                logger.info(f"Заказчик с ИНН {inn} не найден, создаем нового.")
                customer_id = self.database_operations.insert_customer(customer_data, tags_file)
                if customer_id:
                    logger.info(f"Новый заказчик добавлен с ID {customer_id}")
                else:
                    logger.error(f"Не удалось добавить нового заказчика с ИНН {inn}")
        else:
            logger.warning("ИНН не найден в данных.")

        return customer_id

    def parse_links_documentation(self, root, tags, contract_id, tags_file):
        """
        Парсит данные для таблицы links_documentation_44_fz (или 223_fz)
        и вызывает парсинг для таблицы printFormInfo.
        """
        found_tags = []  # Список для хранения данных links_documentation_44_fz или links_documentation_223_fz

        # Работаем с разделом links_documentation из переданных тегов
        links_doc_tags = tags  # Теперь мы используем переданный параметр tags напрямую

        # Обрабатываем ссылки для printFormInfo
        if 'printFormInfo' in links_doc_tags:
            print_form_info = links_doc_tags['printFormInfo']
            xpath = print_form_info.get('xpath')
            if xpath:
                elements = root.findall(xpath)
                for elem in elements:
                    # Извлекаем информацию о файле и ссылке, если они существуют
                    file_name = print_form_info.get('default_file_name', "Извещение о проведении электронного аукциона")
                    url_elem = elem.find(print_form_info.get('document_links'))
                    if url_elem is not None:
                        url = url_elem.text.strip() if url_elem.text else None
                        found_tags.append({
                            "file_name": file_name,
                            "document_links": url,
                            "contract_id": contract_id
                        })

        # Обрабатываем ссылки для attachmentInfo
        if 'attachmentInfo' in links_doc_tags:
            attachment_info = links_doc_tags['attachmentInfo']
            xpath = attachment_info.get('xpath')
            if xpath:
                elements = root.findall(xpath)
                for elem in elements:
                    # Извлекаем информацию о файле и ссылке
                    file_name_elem = elem.find(attachment_info.get('file_name'))
                    url_elem = elem.find(attachment_info.get('document_links'))
                    if file_name_elem is not None and url_elem is not None:
                        file_name = file_name_elem.text.strip() if file_name_elem.text else None
                        url = url_elem.text.strip() if url_elem.text else None
                        if file_name and url:
                            found_tags.append({
                                "file_name": file_name,
                                "document_links": url,
                                "contract_id": contract_id
                            })

        # Вставляем все собранные данные для соответствующей таблицы в базу
        for entry in found_tags:
            if entry:  # Если данные не пустые
                if tags_file == self.tags_paths['get_tags_44_new']:
                    inserted_id = self.database_operations.insert_link_documentation_44_fz(entry)
                elif tags_file == self.tags_paths['get_tags_223_new']:
                    inserted_id = self.database_operations.insert_link_documentation_223_fz(entry)
                else:
                    logger.error(f"Неизвестный файл тегов: {tags_file}")
                    continue
                logger.info(f"Вставленная запись в {tags_file} имеет id: {inserted_id}")

        # Возвращаем все найденные данные
        return found_tags

    def parse_document(self, root, tags):
        """
        Парсит данные для таблицы document.
        """
        found_tags = {}

        for tag, tag_info in tags.items():
            if isinstance(tag_info, dict) and 'xpath' in tag_info:
                xpath = tag_info['xpath']
                element = root.find(xpath)

                if element is not None and element.text:
                    found_tags[tag] = element.text.strip()
                    # logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
                else:
                    found_tags[tag] = None

        return found_tags

    def parse_xml_tags(self, xml_folder_path, region_code, okpd_code):
        """
        Функция для извлечения тегов для каждой таблицы из XML-файлов.
        """
        logger.info(f"Текущий путь: {xml_folder_path}")

        # Определяем, какой JSON файл использовать в зависимости от папки
        if xml_folder_path == self.xml_paths['reest_new_contract_archive_44_fz_xml']:
            tags_file = self.tags_paths['get_tags_44_new']
        # elif xml_folder_path == self.xml_paths['recouped_contract_archive_44_fz_xml']:
        #     tags_file = self.tags_paths['get_tags_44_recouped']
        elif xml_folder_path == self.xml_paths['reest_new_contract_archive_223_fz_xml']:
            tags_file = self.tags_paths['get_tags_223_new']
        # elif xml_folder_path == self.xml_paths['recouped_contract_archive_223_fz_xml']:
        #     tags_file = self.tags_paths['get_tags_223_recouped']
        else:
            logger.error(f"Неизвестная папка: {xml_folder_path}")
            return None

        # Загружаем теги из соответствующего JSON файла
        tags = self.load_json_tags(tags_file)
        if not tags:
            logger.error("Не удалось загрузить теги из JSON.")
            return None

        # Перебираем все XML-файлы в указанной папке
        for xml_file in os.listdir(xml_folder_path):
            if xml_file.endswith(".xml"):
                file_path = os.path.join(xml_folder_path, xml_file)
                logger.info(f"Обрабатываем файл: {file_path}")

                # Загружаем и парсим XML
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()

                    # Удаляем пространства имен перед парсингом
                    cleaned_xml_content = self.remove_namespaces(xml_content)

                    tree = ET.ElementTree(ET.fromstring(cleaned_xml_content))
                    root = tree.getroot()

                except ET.ParseError as e:
                    logger.error(f"Ошибка при парсинге XML-файла {file_path}: {e}")
                    continue

                # Получаем данные о заказчике
                customer_id = self.parse_customer(
                    root,
                    tags.get('customer', {}),
                    tags_file  # Передаем сюда tags_file
                )
                # logger.debug(f'id заказчика: {customer_id}')

                # Получаем данные о торговой площадке
                platform_id = self.parse_trading_platform(root, tags.get('trading_platform', {}))
                # logger.debug(f'id платформы: {platform_id}')

                # Передаем правильные данные для реестра контрактов
                contract_id = self.parse_reestr_contract(
                    root,
                    tags.get('reestr_contract', {}),
                    region_code,
                    okpd_code,
                    customer_id,  # Передаем уже customer_id, а не customer_inn
                    platform_id,
                    tags_file  # Передаем сюда tags_file
                )

                # Парсим данные для таблицы links_documentation_44_fz
                links_documentation = self.parse_links_documentation(
                    root,
                    tags.get('links_documentation', {}),
                    contract_id,
                    tags_file  # Передаем сюда tags_file
                )
                logger.debug(f'Найденные записи для links_documentation_44_fz: {links_documentation}')

                # Если необходимо, добавляй остальные данные, как ссылки и другие формы
                # found_tags.update(self.parse_links_documentation(root, tags.get('links_documentation', {})))
                # found_tags.update(self.parse_print_form_info(root, tags.get('links_documentation', {})))

                # Можно дополнительно сделать запись или другие действия с данными
                logger.info(f"Успешно обработан для файла {xml_file}")

# # # Пример использования
# xml_parser = XMLParser()
# xml_folder_path = r"F:\Программирование\Парсинг ЕИС\223_FZ\xml_reestr_223_fz_new_contracts"  # Укажи нужную папку
# parsed_data = xml_parser.parse_xml_tags(xml_folder_path)
