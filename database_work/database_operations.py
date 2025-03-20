from loguru import logger
from database_work.database_connection import DatabaseManager
from psycopg2 import IntegrityError
from secondary_functions import load_config

class DatabaseOperations:
    def __init__(self, config_path="config.ini"):
        self.db_manager = DatabaseManager()

        self.config = load_config(config_path)
        if not self.config:
            raise ValueError("Ошибка загрузки конфигурации!")

        self.tags_paths = self.config['tags']

    def _prepare_contact(self, customer_data, tags_file):
        """Подготовка поля contact (ФИО) для записи."""
        if tags_file == self.tags_paths['get_tags_44_new']:
            contact_parts = [
                (customer_data.get("contact_last_name") or "").strip(),
                (customer_data.get("contact_first_name") or "").strip(),
                (customer_data.get("contact_middle_name") or "").strip()
            ]
        elif tags_file == self.tags_paths['get_tags_223_new']:
            contact_parts = [
                customer_data.get("contact_last_name") or None,
                customer_data.get("contact_first_name") or None,
                customer_data.get("contact_middle_name") or None
            ]
        else:
            contact_parts = []

        # Убираем пустые строки, заменяем на None
        contact = " ".join([part for part in contact_parts if part]).strip() or None

        return contact

    def _update_field(self, existing_value, new_value):
        """Если новое значение отличается от существующего, добавляем его через ;"""
        if not new_value:  # Если новое значение пустое или None, оставляем старое
            return existing_value
        if existing_value and existing_value != new_value:
            return f"{existing_value}; {new_value}"
        return new_value

    def _is_contact_exists(self, contact):
        """Проверяем, существует ли уже контакт в базе данных."""
        if contact is None:
            return False  # Если контакт равен None, значит, его не существует в базе
        cursor = self.db_manager.cursor
        cursor.execute("""SELECT COUNT(1) FROM customer WHERE contact = %s""", (contact,))
        count = cursor.fetchone()[0]
        return count > 0

    def _insert_data(self, table_name, data):
        """Универсальная функция для вставки данных в любую таблицу."""
        try:
            cursor = self.db_manager.cursor

            # Проверяем и заменяем пустые значения
            for column, value in data.items():
                if value is None or value == '':
                    if column in ['final_price', 'guarantee_amount', 'warranty_size']:
                        data[column] = None
                    elif column in ['start_date', 'end_date']:
                        data[column] = None
                    else:
                        data[column] = None  # Заменяем пустую строку на None

            # Проверка на уникальность контакта
            contact = data.get('contact')
            if contact and self._is_contact_exists(contact):
                logger.warning(f"Контакт {contact} уже существует в базе данных.")
                return None

            logger.debug(f"Вставляем в {table_name} данные: {data}")

            columns = ', '.join(data.keys())
            values = tuple(data.values())
            placeholders = ', '.join(['%s'] * len(data))

            insert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders}) RETURNING id
            """
            cursor.execute(insert_query, values)

            inserted_id = cursor.fetchone()[0]
            self.db_manager.connection.commit()

            logger.info(f"Добавлена новая запись в таблицу {table_name} с id: {inserted_id}")
            return inserted_id

        except IntegrityError as e:
            # Если дубликат уже существует, выбрасываем ошибку и возвращаем None
            logger.warning(f"Ошибка при вставке данных в {table_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при вставке данных в {table_name}: {e}")
            self.db_manager.connection.rollback()
            return None

    def insert_customer(self, customer_data, tags_file):
        """Вставка нового заказчика в таблицу."""
        contact = self._prepare_contact(customer_data, tags_file)
        customer_data['contact'] = contact

        # Удаляем ненужные ключи, которых нет в БД
        customer_data.pop("contact_last_name", None)
        customer_data.pop("contact_first_name", None)
        customer_data.pop("contact_middle_name", None)

        return self._insert_data('customer', customer_data)

    def update_customer(self, customer_data, customer_id, tags_file):
        """Обновление данных заказчика."""
        try:
            cursor = self.db_manager.cursor

            contact = self._prepare_contact(customer_data, tags_file)
            legal_address = customer_data.get("customer_legal_address")
            actual_address = customer_data.get("customer_actual_address")
            phone = customer_data.get("contact_phone")
            email = customer_data.get("contact_email")

            cursor.execute("""
                SELECT contact, contact_phone, contact_email, customer_legal_address, customer_actual_address
                FROM customer WHERE id = %s
            """, (customer_id,))
            existing_customer = cursor.fetchone()

            if existing_customer:
                existing_contact, existing_phone, existing_email, existing_legal_address, existing_actual_address = existing_customer

                update_fields = []
                update_values = []

                if legal_address and legal_address != existing_legal_address:
                    update_fields.append("customer_legal_address = %s")
                    update_values.append(legal_address)

                if actual_address and actual_address != existing_actual_address:
                    update_fields.append("customer_actual_address = %s")
                    update_values.append(actual_address)

                new_contact = self._update_field(existing_contact, contact)
                if new_contact != existing_contact:
                    update_fields.append("contact = %s")
                    update_values.append(new_contact)

                new_phone = self._update_field(existing_phone, phone)
                if new_phone != existing_phone:
                    update_fields.append("contact_phone = %s")
                    update_values.append(new_phone)

                new_email = self._update_field(existing_email, email)
                if new_email != existing_email:
                    update_fields.append("contact_email = %s")
                    update_values.append(new_email)

                if update_fields:
                    update_query = f"""
                        UPDATE customer
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """
                    update_values.append(customer_id)
                    cursor.execute(update_query, tuple(update_values))
                    self.db_manager.connection.commit()
                    logger.info(f"Обновлена запись в customer с id: {customer_id}")
            else:
                logger.warning(f"Запись с id {customer_id} не найдена для обновления.")
                return None

            return customer_id

        except Exception as e:
            logger.error(f"Ошибка при обновлении данных в customer: {e}")
            self.db_manager.connection.rollback()
            return None

    def insert_file_name(self, file_name):
        """Вставляет имя обработанного XML-файла в таблицу file_names_xml."""
        try:
            cursor = self.db_manager.cursor
            insert_query = """
                INSERT INTO file_names_xml (file_name)
                VALUES (%s) RETURNING id;
            """
            cursor.execute(insert_query, (file_name,))
            inserted_id = cursor.fetchone()[0]
            self.db_manager.connection.commit()

            logger.info(f"Добавлено имя файла в file_names_xml с id: {inserted_id}")
            return inserted_id

        except IntegrityError as e:
            logger.warning(f"Ошибка при вставке имени файла {file_name} в file_names_xml: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при вставке имени файла {file_name}: {e}")
            self.db_manager.connection.rollback()
            return None

    # Пример вставки в другие таблицы, аналогично insert_customer
    def insert_trading_platform(self, trading_platform_data):
        return self._insert_data('trading_platform', trading_platform_data)

    def insert_reestr_contract_44_fz(self, contract_data):
        return self._insert_data('reestr_contract_44_fz', contract_data)

    def insert_link_documentation_44_fz(self, links_44_fz_data):
        return self._insert_data('links_documentation_44_fz', links_44_fz_data)

    def insert_reestr_contract_223_fz(self, contract_data):
        return self._insert_data('reestr_contract_223_fz', contract_data)

    def insert_link_documentation_223_fz(self, links_44_fz_data):
        return self._insert_data('links_documentation_223_fz', links_44_fz_data)
