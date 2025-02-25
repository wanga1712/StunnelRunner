import os
import json
import xml.etree.ElementTree as ET
from loguru import logger
import re

from secondary_functions import load_config

class XMLParser:
    """
    Класс для обработки XML-файлов в указанной директории.
    """

    def __init__(self, config_path="config.ini"):
        """
        Загружает конфигурацию и путь к XML-файлам из config.ini.
        """
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

    def parse_reestr_contract(self, root, tags):
        """
        Парсит данные для таблицы reestr_contract_44_fz.
        """
        found_tags = {}

        for tag, xpath in tags.items():
            # Убираем пространство имен из пути
            tag_without_namespace = xpath.split(":")[-1]

            # Ищем тег на любом уровне
            elements = root.findall(f".//{tag_without_namespace}")

            if elements:
                values = [elem.text.strip() for elem in elements if elem.text and elem.text.strip()]
                found_tags[tag] = "; ".join(values) if values else None
                if values:
                    logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
            else:
                found_tags[tag] = None

        return found_tags

    def parse_trading_platform(self, root, tags):
        """
        Парсит данные для таблицы trading_platform.
        """
        found_tags = {}

        for tag, xpath in tags.items():
            element = root.find(f".//{xpath}")  # Добавляем ".//" для поиска на любом уровне

            if element is not None and element.text:
                found_tags[tag] = element.text.strip()
                logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
            else:
                found_tags[tag] = None

        return found_tags

    def parse_customer(self, root, tags):
        """
        Парсит данные для таблицы customer.
        """
        found_tags = {}

        for tag, xpath in tags.items():
            element = root.find(f".//{xpath}")  # Добавляем ".//" для поиска на любом уровне

            if element is not None and element.text:
                found_tags[tag] = element.text.strip()
                logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
            else:
                found_tags[tag] = None

        return found_tags

    def parse_links_documentation(self, root, tags):
        """
        Парсит данные для таблицы links_documentation_44_fz.
        """
        found_tags = {}

        for tag, tag_info in tags.items():
            if isinstance(tag_info, dict) and 'xpath' in tag_info:
                # Получаем XPath для поиска
                xpath = tag_info['xpath']
                elements = root.findall(xpath)  # Находим все элементы, соответствующие XPath

                for elem in elements:
                    # Для каждого найденного элемента извлекаем данные по указанным тегам
                    file_name_tag = tag_info.get('fileName_tag')
                    url_tag = tag_info.get('url_tag')

                    if file_name_tag and url_tag:
                        file_name_elem = elem.find(file_name_tag)
                        url_elem = elem.find(url_tag)

                        # Если найдено значение, добавляем его в результат
                        if file_name_elem is not None and url_elem is not None:
                            file_name = file_name_elem.text.strip() if file_name_elem.text else None
                            url = url_elem.text.strip() if url_elem.text else None
                            if file_name and url:
                                found_tags[tag] = {
                                    "file_name": file_name,
                                    "url": url
                                }
                                logger.info(f"Тег: {tag} содержит значение: {file_name}, {url}")
                            else:
                                found_tags[tag] = None
                        else:
                            found_tags[tag] = None

        return found_tags

    def parse_print_form_info(self, root, tags):
        """
        Парсит данные для таблицы printFormInfo.
        """
        found_tags = {}

        for tag, tag_info in tags.items():
            if isinstance(tag_info, dict) and 'xpath' in tag_info:
                xpath = tag_info['xpath']
                element = root.find(xpath)

                if element is not None:
                    # Получаем ссылку
                    link = element.text.strip() if element.text else None

                    # Если ссылка пуста
                    if not link:
                        continue  # Просто пропускаем пустые ссылки

                    # Проверяем наличие имени файла, если его нет — используем значение по умолчанию
                    file_name = tag_info.get('default_file_name', 'Неизвестное имя файла')

                    if link:
                        found_tags[tag] = {
                            "file_name": file_name,
                            "url": link
                        }
                        logger.info(f"Тег: {tag} содержит ссылку: {link} и имя файла: {file_name}")
                    else:
                        found_tags[tag] = {
                            "file_name": file_name,
                            "url": None
                        }
                else:
                    found_tags[tag] = {
                        "file_name": None,
                        "url": None
                    }

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
                    logger.info(f"Тег: {tag} содержит значение: {found_tags[tag]}")
                else:
                    found_tags[tag] = None

        return found_tags

    def parse_xml_tags(self, xml_folder_path):
        """
        Функция для извлечения тегов для каждой таблицы из XML-файлов.
        """
        logger.info(f"Текущий путь: {xml_folder_path}")

        # Определяем, какой JSON файл использовать в зависимости от папки
        if xml_folder_path == self.xml_paths['reest_new_contract_archive_44_fz_xml']:
            tags_file = self.tags_paths['get_tags_44_new']
        elif xml_folder_path == self.xml_paths['recouped_contract_archive_44_fz_xml']:
            tags_file = self.tags_paths['get_tags_44_recouped']
        elif xml_folder_path == self.xml_paths['reest_new_contract_archive_223_fz_xml']:
            tags_file = self.tags_paths['get_tags_223_new']
        elif xml_folder_path == self.xml_paths['recouped_contract_archive_223_fz_xml']:
            tags_file = self.tags_paths['get_tags_223_recouped']
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

                # Парсим каждую таблицу отдельно
                found_tags = {}
                found_tags.update(self.parse_reestr_contract(root, tags.get('reestr_contract', {})))
                found_tags.update(self.parse_trading_platform(root, tags.get('trading_platform', {})))
                found_tags.update(self.parse_customer(root, tags.get('customer', {})))
                found_tags.update(self.parse_links_documentation(root, tags.get('links_documentation', {})))
                found_tags.update(self.parse_print_form_info(root, tags.get('links_documentation', {})))

        return "Парсинг завершён."

# # # Пример использования
# xml_parser = XMLParser()
# xml_folder_path = r"F:\Программирование\Парсинг ЕИС\223_FZ\xml_reestr_223_fz_new_contracts"  # Укажи нужную папку
# parsed_data = xml_parser.parse_xml_tags(xml_folder_path)
