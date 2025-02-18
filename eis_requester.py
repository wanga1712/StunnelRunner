from loguru import logger
from datetime import datetime, timezone
import uuid
import requests

from secondary_functions import get_region_codes, load_token, load_config
from utils import XMLParser  # Импорт класса с функцией extract_archive_urls
from file_downloader import FileDownloader  # Импорт класса с функцией download_files


class EISRequester:
    def __init__(self, config_path="config.ini"):
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        self.url = "http://localhost:8080/eis-integration/services/getDocsIP"

        # Загружаем токен
        self.token = load_token(self.config)

        # Настройки из конфигурации
        self.date = self.config.get("eis", "date")
        logger.info(f"Дата: {self.date}")

        # Получаем регионы с помощью get_region_codes
        regions_file = self.config.get("path", "regions_file", fallback=None)
        self.regions = get_region_codes(regions_file)

        # Получаем подсистемы для запроса по 44ФЗ из конфигурации
        self.subsystems_44 = [s.strip() for s in self.config.get("eis", "subsystems_44").split(",")]
        # logger.info(f"Подсистемы 44ФЗ: {self.subsystems_44}")

        # Получаем типы документов для подсистемы 'извещения о закупках'
        self.documentType44_PRIZ = [doc.strip() for doc in self.config.get("eis", "documentType44_PRIZ").split(",")]
        # logger.info(f'извещения 44ФЗ {self.documentType44_PRIZ}')

        # Получаем типы документов для подсистемы 'протоколы подведения итогов'
        self.documentType44_RGK = [doc.strip() for doc in self.config.get("eis", "documentType44_RGK").split(",")]
        # logger.info(f'протоколы 44ФЗ {self.documentType44_RGK}')

        # Получаем подсистемы для запроса по 223ФЗ из конфигурации
        self.subsystems_223 = [s.strip() for s in self.config.get("eis", "subsystems_223").split(",")]
        # logger.info(f"Подсистемы 223ФЗ: {self.subsystems_223}")

        # Получаем типы документов для подсистемы 'извещения о закупках'
        self.documentType223_RI223 = [doc.strip() for doc in self.config.get("eis", "documentType223_RI223").split(",")]
        # logger.info(f'извещения 223ФЗ {self.documentType223_RI223}')

        # Получаем типы документов для подсистемы 'протоколы подведения итогов'
        self.documentType223_RD223 = [doc.strip() for doc in self.config.get("eis", "documentType223_RD223").split(",")]
        # logger.info(f'протоколы 223ФЗ {self.documentType223_RD223}')

        self.xml_parser = XMLParser()  # Создаём объект для парсинга XML
        self.file_downloader = FileDownloader()  # Создаём объект для скачивания файлов

    def get_current_time_utc(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def generate_soap_request(self, region_code, subsystem, document_type):
        """Генерирует SOAP-запрос"""
        region_code_str = str(region_code).zfill(2)

        id_value = str(uuid.uuid4())
        current_time = self.get_current_time_utc()

        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:ws="http://zakupki.gov.ru/fz44/get-docs-ip/ws">
            <soapenv:Header>
                <individualPerson_token>{self.token}</individualPerson_token>
            </soapenv:Header>
            <soapenv:Body>
                <ws:getDocsByOrgRegionRequest>
                    <index>
                        <id>{id_value}</id>
                        <createDateTime>{current_time}</createDateTime>
                        <mode>PROD</mode>
                    </index>
                    <selectionParams>
                        <orgRegion>{region_code_str}</orgRegion>
                        <subsystemType>{subsystem}</subsystemType>
                        <documentType44>{document_type}</documentType44>
                        <periodInfo>
                            <exactDate>{self.date}</exactDate>
                        </periodInfo>
                    </selectionParams>
                </ws:getDocsByOrgRegionRequest>
            </soapenv:Body>
        </soapenv:Envelope>
        """

        logger.info(
            f"Запрос для региона {region_code_str}, подсистемы {subsystem}, документа {document_type} сформирован.")

        return soap_request

    def send_soap_request(self, soap_request, region_code, document_type):
        """Отправляет SOAP-запрос и возвращает ответ"""
        headers = {
            "Content-Type": "text/xml",
            "Authorization": f"Bearer {self.token}"
        }

        logger.info("Отправка SOAP-запроса...")
        try:
            response = requests.post(self.url, data=soap_request.encode("utf-8"), headers=headers, verify=False)
            response.raise_for_status()
            logger.info(f"Ответ от сервера получен.")

            # Парсим XML, извлекаем ссылки на архивы
            archive_urls = self.xml_parser.extract_archive_urls(response.text)
            if archive_urls:
                logger.info(f"Найдено {len(archive_urls)} ссылок на архивы. Начинаем загрузку...")
                self.file_downloader.download_files(archive_urls, document_type)
            else:
                logger.warning(f"Ссылки на архивы не найдены. Ответ сервера: {response.text}")

            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении SOAP-запроса: {e}")
            return None

    def process_requests(self):
        """Обрабатывает все запросы по всем регионам, подсистемам и типам документов"""
        try:
            # Перебираем регионы
            for region_code in self.regions:
                logger.info(f"Начинаем обработку региона {region_code}")
                # Перебираем подсистемы для 44ФЗ
                for subsystem in self.subsystems_44:
                    if subsystem == "PRIZ":
                        # Перебираем документы для PRIZ
                        for document_type in self.documentType44_PRIZ:
                            soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                            if soap_request:
                                logger.info(f"Запрос для PRIZ ({document_type}) успешно сформирован.")
                                # Передаем запрос в send_soap_request с необходимыми параметрами
                                self.send_soap_request(soap_request, region_code, document_type)
                            else:
                                logger.error(f"Не удалось сформировать запрос для PRIZ ({document_type}).")

                    elif subsystem == "RGK":
                        # Перебираем документы для RGK
                        for document_type in self.documentType44_RGK:
                            soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                            if soap_request:
                                logger.info(f"Запрос для RGK ({document_type}) успешно сформирован.")
                                # Передаем запрос в send_soap_request с необходимыми параметрами
                                self.send_soap_request(soap_request, region_code, document_type)
                            else:
                                logger.error(f"Не удалось сформировать запрос для RGK ({document_type}).")

                    # Перебираем подсистемы для 223ФЗ
                    for subsystem in self.subsystems_223:
                        if subsystem == "RI223":
                            # Перебираем документы для RI223
                            for document_type in self.documentType223_RI223:
                                soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                                if soap_request:
                                    logger.info(f"Запрос для RI223 ({document_type}) успешно сформирован.")
                                    # Передаем запрос в send_soap_request с необходимыми параметрами
                                    self.send_soap_request(soap_request, region_code, document_type)
                                else:
                                    logger.error(f"Не удалось сформировать запрос для RI223 ({document_type}).")

                        elif subsystem == "RD223":
                            # Перебираем документы для RD223
                            for document_type in self.documentType223_RD223:
                                soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                                if soap_request:
                                    logger.info(f"Запрос для RD223 ({document_type}) успешно сформирован.")
                                    # Передаем запрос в send_soap_request с необходимыми параметрами
                                    self.send_soap_request(soap_request, region_code, document_type)
                                else:
                                    logger.error(f"Не удалось сформировать запрос для RD223 ({document_type}).")

        except Exception as e:
            logger.error(f"Ошибка при обработке запросов: {e}")


# Тестирование
if __name__ == "__main__":
    eis_requester = EISRequester(config_path="config.ini")
    eis_requester.process_requests()
