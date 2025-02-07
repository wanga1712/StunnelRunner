import subprocess
from loguru import logger
import os
import configparser


class StunnelRunner:
    def __init__(self, config_file: str):
        # Загружаем конфигурационный файл
        self.config = self.load_config(config_file)

        # Получаем настройки из конфигурационного файла
        self.stunnel_dir = self.config.get('stunnel', 'stunnel_dir')
        self.config_file = self.config.get('stunnel', 'config_file')

    def load_config(self, config_file):
        """Загружает конфигурационный файл."""
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        return config

    def run_stunnel(self):
        """Запускает stunnel с конфигурационным файлом и перенаправляет логи в файл."""
        # Формируем команду для запуска stunnel с конфигом
        command = f".\\stunnel_msspi.exe .\\{self.config_file} > stunnel.log 2>&1"

        # Путь к директории, где находится stunnel_msspi.exe и конфиг
        os.chdir(self.stunnel_dir)

        try:
            # Выполняем команду через subprocess
            logger.info(f"Запускаю stunnel: {command}")
            proc = subprocess.Popen(command, cwd=self.stunnel_dir, shell=True)
            proc.communicate()  # Дожидаемся завершения процесса

            # Проверяем код завершения процесса
            if proc.returncode == 0:
                logger.info("stunnel успешно запущен.")
            else:
                logger.error(f"stunnel завершился с кодом {proc.returncode}.")

        except Exception as e:
            logger.error(f"Ошибка при запуске stunnel: {e}")
            return None
