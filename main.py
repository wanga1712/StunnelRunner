from stunnel_runner import StunnelRunner


# Запуск
if __name__ == "__main__":

    stunnel_runner = StunnelRunner("config.ini")
    stunnel_runner.run_stunnel()
