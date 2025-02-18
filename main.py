from stunnel_runner import StunnelRunner
from eis_requester import EISRequester


# Запуск
if __name__ == "__main__":

    stunnel_runner = StunnelRunner()
    stunnel_runner.run_stunnel()

    # Создаем экземпляр EISRequester и запускаем обработку запросов
    eis_requester = EISRequester()
    eis_requester.process_requests()  # Запуск обработки запросов

