import os
import time
from loguru import logger
from stunnel_runner import StunnelRunner
from eis_requester import EISRequester

# Пути к папкам с архивами
folders = {
    "44 ФЗ (реестр контрактов)": r"F:\Программирование\Парсинг ЕИС\44_FZ\xml_reestr_44_fz_new_contracts",
    "44 ФЗ (разыгранные контракты)": r"F:\Программирование\Парсинг ЕИС\44_FZ\xml_reestr_44_new_contracts_recouped",
    "223 ФЗ (реестр контрактов)": r"F:\Программирование\Парсинг ЕИС\223_FZ\xml_reestr_223_fz_new_contracts",
    "223 ФЗ (разыгранные контракты)": r"F:\Программирование\Парсинг ЕИС\223_FZ\xml_reestr_new_223_contracts_recouped",
}

# Расширения архивных файлов
archive_extensions = {".zip", ".rar", ".7z", ".tar", ".gz"}

def get_folder_size(folder_path):
    """Вычисляет общий размер архивных файлов в папке."""
    total_size = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in archive_extensions):
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
    return total_size

if __name__ == "__main__":
    start_time = time.time()  # Засекаем время начала работы
    logger.info("Запуск программы...")

    # Запуск Stunnel
    stunnel_runner = StunnelRunner()
    stunnel_runner.run_stunnel()
    logger.info("Stunnel успешно запущен.")

    # Запуск обработки запросов
    eis_requester = EISRequester()
    eis_requester.process_requests()
    logger.info("Обработка запросов завершена.")

    # Подсчет размера скачанных архивов
    total_downloaded_size = 0
    for folder_name, folder_path in folders.items():
        if os.path.exists(folder_path):
            folder_size = get_folder_size(folder_path)
            total_downloaded_size += folder_size
            logger.info(f"Объем архивных файлов в '{folder_name}': {folder_size / (1024 * 1024):.2f} МБ")
        else:
            logger.warning(f"Папка '{folder_name}' не найдена!")

    logger.info(f"Общий объем скачанных архивных файлов: {total_downloaded_size / (1024 * 1024):.2f} МБ")

    # Засекаем время окончания работы
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Перевод в часы и минуты
    elapsed_hours = int(elapsed_time // 3600)
    elapsed_minutes = int((elapsed_time % 3600) // 60)

    logger.info(f"Время выполнения программы: {elapsed_hours} ч {elapsed_minutes} мин")
