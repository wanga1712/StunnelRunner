import subprocess
from loguru import logger
import os


class StunnelRunner:
    def __init__(self, stunnel_dir: str, config_file: str):
        self.stunnel_dir = stunnel_dir
        self.config_file = config_file

    def run_stunnel(self):
        """Запускает stunnel с конфигурационным файлом и перенаправляет логи в файл."""
        # Формируем команду для запуска stunnel с конфигом
        command = f".\\stunnel_msspi.exe .\\{self.config_file} > stunnel.log 2>&1"

        # Путь к директории, где находится stunnel_msspi.exe и конфиг
        os.chdir(self.stunnel_dir)

        try:
            # Выполняем команду через subprocess
            logger.info(f"Выполнение команды: {command}")
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