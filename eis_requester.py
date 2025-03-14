from loguru import logger
from datetime import datetime, timezone
import uuid
import requests

from secondary_functions import load_token, load_config
from database_work.database_requests import get_region_codes
from utils import XMLParser  # Импорт класса с функцией extract_archive_urls
from file_downloader import FileDownloader  # Импорт класса с функцией download_files


class EISRequester:
    def __init__(self, config_path: str = "config.ini"):
        """
        Инициализация объекта EISRequester.

        Загружает настройки из конфигурационного файла, токен для авторизации,
        информацию о регионах, подсистемах и типах документов для работы с ЕИС.

        :param config_path: Путь к конфигурационному файлу. По умолчанию "config.ini".
        :raises ValueError: Если загрузка конфигурации не удалась.
        """
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        self.url = "http://localhost:8080/eis-integration/services/getDocsIP"  # URL для запроса к ЕИС

        # Загружаем токен для доступа к сервису
        self.token = load_token(self.config)

        # Загружаем дату из конфигурации
        self.date = self.config.get("eis", "date")
        logger.info(f"Дата: {self.date}")  # Логируем текущую дату

        # Получаем список регионов из файла с кодами регионов
        self.regions = get_region_codes()

        # Загружаем подсистемы для запроса по 44-ФЗ из конфигурации
        self.subsystems_44 = [s.strip() for s in self.config.get("eis", "subsystems_44").split(",")]

        # Загружаем типы документов для подсистемы 'Извещения о закупках' по 44-ФЗ
        self.documentType44_PRIZ = [doc.strip() for doc in self.config.get("eis", "documentType44_PRIZ").split(",")]

        # Загружаем типы документов для подсистемы 'Протоколы подведения итогов' по 44-ФЗ
        self.documentType44_RGK = [doc.strip() for doc in self.config.get("eis", "documentType44_RGK").split(",")]

        # Загружаем подсистемы для запроса по 223-ФЗ из конфигурации
        self.subsystems_223 = [s.strip() for s in self.config.get("eis", "subsystems_223").split(",")]

        # Загружаем типы документов для подсистемы 'Извещения о закупках' по 223-ФЗ
        self.documentType223_RI223 = [doc.strip() for doc in self.config.get("eis", "documentType223_RI223").split(",")]

        # Загружаем типы документов для подсистемы 'Протоколы подведения итогов' по 223-ФЗ
        self.documentType223_RD223 = [doc.strip() for doc in self.config.get("eis", "documentType223_RD223").split(",")]

        # Создаём объект для парсинга XML
        self.xml_parser = XMLParser()

        # Создаём объект для скачивания файлов
        self.file_downloader = FileDownloader()

    def get_current_time_utc(self) -> str:
        """
        Получает текущее время в формате UTC.

        :return: Текущее время в формате "YYYY-MM-DDTHH:MM:SSZ"
        """
        # Возвращаем текущее время в UTC в нужном формате
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def generate_soap_request(self, region_code: int, subsystem: str, document_type: str) -> str:
        """
        Генерирует SOAP-запрос для получения документов из ЕИС.

        :param region_code: Код региона для запроса.
        :param subsystem: Подсистема (например, 44ФЗ или 223ФЗ) для запроса.
        :param document_type: Тип документа (например, извещение или протокол).
        :return: Сформированный SOAP-запрос в виде строки.
        """

        # Генерация уникального идентификатора для запроса
        id_value = str(uuid.uuid4())
        # Получаем текущее время в формате UTC
        current_time = self.get_current_time_utc()

        # Формируем SOAP-запрос в формате XML
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
                        <orgRegion>{region_code}</orgRegion>
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

        # Логируем информацию о сформированном запросе
        logger.info(
            f"Запрос для региона {region_code}, подсистемы {subsystem}, документа {document_type} сформирован.")

        # Возвращаем сформированный SOAP-запрос
        return soap_request

    def send_soap_request(self, soap_request: str, region_code: int, document_type: str, subsystem: str) -> str:
        """
        Отправляет SOAP-запрос к серверу и обрабатывает полученный ответ.

        :param soap_request: Сформированный SOAP-запрос в виде строки.
        :param region_code: Код региона, связанный с запросом (не используется напрямую в этом методе).
        :param document_type: Тип документа, который был запрашиваемым.
        :return: Ответ сервера в виде строки, если запрос успешен; None, если произошла ошибка.
        """
        # Заголовки для отправки запроса
        headers = {
            "Content-Type": "text/xml",  # Устанавливаем тип контента как XML
            "Authorization": f"Bearer {self.token}"  # Токен авторизации в заголовках
        }

        logger.info("Отправка SOAP-запроса...")  # Логируем начало отправки запроса
        try:
            # Отправка POST-запроса с SOAP-данными
            response = requests.post(self.url, data=soap_request.encode("utf-8"), headers=headers, verify=False)
            response.raise_for_status()  # Проверяем, что запрос завершился успешно
            logger.info(f"Ответ от сервера получен.")  # Логируем успешный ответ

            # Парсим XML-ответ и извлекаем ссылки на архивы
            archive_urls = self.xml_parser.extract_archive_urls(response.text)
            if archive_urls:
                # Логируем, если найдены ссылки на архивы, и начинаем их загрузку
                logger.info(f"Найдено {len(archive_urls)} ссылок на архивы. Начинаем загрузку...")
                self.file_downloader.download_files(archive_urls, subsystem, region_code)  # Загружаем файлы
                logger.debug(f"Download if {subsystem}")
            else:
                # Логируем, если ссылки на архивы не найдены
                logger.warning(f"Ссылки на архивы не найдены. Ответ сервера: {response.text}")

            return response.text  # Возвращаем текст ответа от сервера
        except requests.exceptions.RequestException as e:
            # Логируем ошибку при выполнении запроса
            logger.error(f"Ошибка при выполнении SOAP-запроса: {e}")
            return None  # Возвращаем None в случае ошибки

    def process_requests(self):
        """
        Обрабатывает все запросы по всем регионам, подсистемам и типам документов.

        Перебирает регионы, подсистемы и типы документов для 44-ФЗ и 223-ФЗ, генерирует и отправляет SOAP-запросы.
        В случае ошибок при формировании запросов или отправке они логируются.
        """
        try:
            # Перебираем регионы
            for region_code in self.regions:
                logger.info(f"Начинаем обработку региона {region_code}")  # Логируем начало обработки региона
                # Перебираем подсистемы для 44ФЗ
                for subsystem in self.subsystems_44:
                    if subsystem == "PRIZ":
                        # Перебираем документы для PRIZ
                        for document_type in self.documentType44_PRIZ:
                            soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                            if soap_request:
                                logger.info(
                                    f"Запрос для PRIZ ({document_type}) успешно сформирован.")  # Логируем успешное формирование запроса
                                # Передаем запрос в send_soap_request с необходимыми параметрами
                                self.send_soap_request(soap_request, region_code, document_type, subsystem)
                            else:
                                logger.error(
                                    f"Не удалось сформировать запрос для PRIZ ({document_type}).")  # Логируем ошибку при формировании запроса

                    elif subsystem == "RGK":
                        # Перебираем документы для RGK
                        for document_type in self.documentType44_RGK:
                            soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                            if soap_request:
                                logger.info(
                                    f"Запрос для RGK ({document_type}) успешно сформирован.")  # Логируем успешное формирование запроса
                                # Передаем запрос в send_soap_request с необходимыми параметрами
                                self.send_soap_request(soap_request, region_code, document_type, subsystem)
                            else:
                                logger.error(
                                    f"Не удалось сформировать запрос для RGK ({document_type}).")  # Логируем ошибку при формировании запроса

                    # Перебираем подсистемы для 223ФЗ
                    for subsystem in self.subsystems_223:
                        if subsystem == "RI223":
                            # Перебираем документы для RI223
                            for document_type in self.documentType223_RI223:
                                soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                                if soap_request:
                                    logger.info(
                                        f"Запрос для RI223 ({document_type}) успешно сформирован.")  # Логируем успешное формирование запроса
                                    # Передаем запрос в send_soap_request с необходимыми параметрами
                                    self.send_soap_request(soap_request, region_code, document_type, subsystem)
                                else:
                                    logger.error(
                                        f"Не удалось сформировать запрос для RI223 ({document_type}).")  # Логируем ошибку при формировании запроса

                        elif subsystem == "RD223":
                            # Перебираем документы для RD223
                            for document_type in self.documentType223_RD223:
                                soap_request = self.generate_soap_request(region_code, subsystem, document_type)
                                if soap_request:
                                    logger.info(
                                        f"Запрос для RD223 ({document_type}) успешно сформирован.")  # Логируем успешное формирование запроса
                                    # Передаем запрос в send_soap_request с необходимыми параметрами
                                    self.send_soap_request(soap_request, region_code, document_type, subsystem)
                                else:
                                    logger.error(
                                        f"Не удалось сформировать запрос для RD223 ({document_type}).")  # Логируем ошибку при формировании запроса

        except Exception as e:
            logger.error(f"Ошибка при обработке запросов: {e}")  # Логируем ошибку при обработке запросов


# Тестирование
if __name__ == "__main__":
    eis_requester = EISRequester(config_path="config.ini")
    eis_requester.process_requests()
