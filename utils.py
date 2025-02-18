from loguru import logger
from lxml import etree
from xml.etree import ElementTree as ET

class XMLParser:
    @staticmethod
    def extract_archive_urls(xml_content):
        try:
            # Используем ElementTree, передавая bytes вместо строки
            root = ET.fromstring(xml_content.encode("utf-8"))
            # Используем lxml для поиска archiveUrl
            tree = etree.fromstring(xml_content.encode("utf-8"))
            urls = [url.text for url in tree.xpath("//archiveUrl")]

            return urls
        except Exception as e:
            logger.error(f"Ошибка при парсинге XML: {e}")
            return []

