import json

# Функция для загрузки данных о регионах из JSON файла
def load_regions(filename="regions.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

# Получаем регионы из файла
regions_dict = load_regions()

# Пример использования
def get_region_name(region_number):
    return regions_dict.get(str(region_number), "Неизвестный регион")