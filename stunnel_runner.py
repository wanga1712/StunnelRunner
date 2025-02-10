import subprocess
from loguru import logger
import os

from secondary_functions import load_config


class StunnelRunner:
    def __init__(self, config_path="config.ini"):
        # Загружаем настройки из конфигурации
        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        # Получаем настройки из конфигурационного файла
        self.stunnel_dir = self.config.get('stunnel', 'stunnel_dir', fallback=".")
        self.config_file = self.config.get('stunnel', 'config_file', fallback="stunnel.conf")

        # Проверяем существование stunnel_msspi.exe
        self.stunnel_exe = os.path.join(self.stunnel_dir, "stunnel_msspi.exe")
        if not os.path.exists(self.stunnel_exe):
            raise FileNotFoundError(f"Файл {self.stunnel_exe} не найден! Проверьте путь в конфигурации.")

    def run_stunnel(self):
        """Запускает stunnel с конфигурационным файлом и перенаправляет логи."""
        command = [self.stunnel_exe, self.config_file]

        try:
            logger.info(f"Запускаю stunnel: {' '.join(command)} в {self.stunnel_dir}")

            with open(os.path.join(self.stunnel_dir, "stunnel.log"), "w") as log_file:
                proc = subprocess.Popen(command, cwd=self.stunnel_dir, stdout=log_file, stderr=subprocess.STDOUT)

            logger.info("stunnel успешно запущен (процесс выполняется в фоне).")

            return proc  # Возвращаем объект процесса, если нужно контролировать выполнение

        except Exception as e:
            logger.error(f"Ошибка при запуске stunnel: {e}")
            return None
