from stunnel_runner import StunnelRunner


# Запуск
if __name__ == "__main__":
    stunnel_dir = r"E:\Программирование\Парсинг ЕИС\stunel"  # Путь к директории с stunnel
    config_file = "stunnel.conf"  # Название конфигурационного файла

    stunnel_runner = StunnelRunner(stunnel_dir, config_file)
    stunnel_runner.run_stunnel()
