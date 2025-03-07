# Старт с StunnelRunner

## Описание
Модуль StunnelRunner предназначен для запуска утилиты stunnel_msspi.exe
с указанным конфигурационным файлом, перенаправляя логи в файл для последующего анализа.
Этот модуль полезен для автоматизации процесса подключения через stunnel,
что используется для безопасных соединений в рамках различных приложений.

## Установка
Скачайте и установите Stunnel на свой компьютер.
Скопируйте необходимые файлы, включая stunnel_msspi.exe и конфигурационный файл stunnel.conf, в папку проекта.
Убедитесь, что Python 3.9 установлен на вашей системе.
Установите необходимые зависимости:
```
pip install loguru
```

## Использование
#### 1. Подключение модуля
Для использования класса StunnelRunner создайте новый Python файл и импортируйте класс:
```
from stunnel_runner import StunnelRunner
```
#### 2. Настройка и запуск
- Для того чтобы запустить stunnel, вам необходимо передать путь к директории с stunnel_msspi.exe
и конфигурационному файлу stunnel.conf.
- Перед использованием необходимо настроить файл конфигурации `config.ini`
с нужными значениями и установить токен в файле `.env`.

## Пример использования:
```
from stunnel_runner import StunnelRunner

# Настройка
if __name__ == "__main__":
    stunnel_dir = r"E:\Программирование\Парсинг ЕИС\stunel"  # Путь к директории с stunnel
    config_file = "stunnel.conf"  # Название конфигурационного файла

    # Создание экземпляра и запуск
    stunnel_runner = StunnelRunner(stunnel_dir, config_file)
    stunnel_runner.run_stunnel()
```
3. Логи
Логи выполнения команды stunnel будут записаны в файл stunnel.log. Вы можете использовать этот файл для диагностики ошибок, таких как неверный путь, неправильная конфигурация или проблемы с запуском.

4. Примечания
Убедитесь, что пути указаны корректно, и используйте абсолютные пути для большей уверенности.
Запуск происходит в командной оболочке (через cmd.exe), что позволяет работать с относительными путями.

## Структура базы данных
База данных содержит 16 таблиц:

- region — справочник регионов.
- dates — даты внесения данных.
- file_names_xml — названия XML-файлов.
- customer — информация о заказчиках.
- contractor — информация о подрядчиках.
- trading_platform — торговые площадки.
- collection_codes_okpd — классификатор ОКПД.
- reestr_contract_44_fz — контракты по 44-ФЗ.
- links_documentation_44_fz — ссылки на документацию 44-ФЗ.
- reestr_contract_223_fz — контракты по 223-ФЗ.
- links_documentation_223_fz — ссылки на документацию 223-ФЗ.
- stop_words_names — стоп-слова.
- key_words_names — ключевые слова.
- key_words_names_documentations — ключевые слова в документации.
- users — информация о пользователях.
- okpd_from_users — ОКПД пользователей.

🔗 Связи между таблицами
- region ↔ customer (по региону заказчика).
- customer ↔ reestr_contract_44_fz / reestr_contract_223_fz (контракты заказчика).
- trading_platform ↔ reestr_contract_44_fz / reestr_contract_223_fz (на какой площадке проводились торги).
- contractor ↔ reestr_contract_44_fz / reestr_contract_223_fz (кто является подрядчиком по контракту).
- collection_codes_okpd ↔ reestr_contract_44_fz / reestr_contract_223_fz (код ОКПД контракта).
- links_documentation_44_fz ↔ reestr_contract_44_fz (ссылки на документацию по 44-ФЗ).
- links_documentation_223_fz ↔ reestr_contract_223_fz (ссылки на документацию по 223-ФЗ).
- stop_words_names, key_words_names, key_words_names_documentations ↔ users (пользовательские настройки фильтрации).
- okpd_from_users ↔ reestr_contract_44_fz / reestr_contract_223_fz (пользовательские настройки поиска по ОКПД).

📌 Использование базы данных
1. Запустите PostgreSQL сервер.
2. Создайте базу данных с помощью CREATE DATABASE Tender_Monitor;
3. Запустите SQL-скрипт для создания таблиц.
4. Начните добавлять и анализировать данные.

GNU GENERAL PUBLIC LICENSE
Version 3, 07 February 2025
...
