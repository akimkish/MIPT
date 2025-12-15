import json

SIMILARITY_THRESHOLD = 0.8  # Порог схожести: число от 0 до 1. Значение 0.8 означает, что товары считаются дубликатами при 80% схожести.
USE_PREPROCESSING = True  # Флаг предобработки: включить нормализацию текста.

# Словарь синонимов и второстепенных слов, словарь составлен для частного случая - данных из файлов catalog.txt и new_items.txt.
# При необходимости словарь обновляется.
synonyms = {
    "гб": "gb",
    "гб.": "gb",
    "гбайт": "gb",
    "черный": "black",
    "чёрный": "black",
    "черная": "black",
    "синий": "blue",
    "синяя": "blue",
    "дюйм": '"',
    "дюйма": '"',
    "дюймов": '"',
    "робот-пылесос": " ",
    "robot": " ",
    "vacuum": " ",
    "cleaner": " ",
    "смартфон": " ",
    "телефон": " ",
    "планшет": " ",
}


def levenshtein_distance(item1: str, item2: str) -> int:
    """Метод расстояния редактирования Левенштейна для выявления дублирующих значений
    Расстояние Левенштейна измеряет минимальное количество операций редактирования
    (вставка, удаление, замена), необходимых для преобразования одной строки в другую.
    """
    n = len(item1) + 1
    m = len(item2) + 1
    dp = [[0] * m for _ in range(n)]
    for i in range(n):
        dp[i][0] = i
    for j in range(m):
        dp[0][j] = j
    for i in range(1, n):
        for j in range(1, m):
            cost = 0 if item1[i - 1] == item2[j - 1] else 1
            dp[i][j] = min(
                [dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost]
            )
    return dp[n - 1][m - 1]


def similarity(item1, item2):
    """Вычисляет схожесть на основе расстояния редактирования Левенштейна
    (1 - расстояние редактирования Левенштейна / максимальная длина наименования товара)
    """
    if not item1 and not item2:
        return 1.0
    dist = levenshtein_distance(item1, item2)
    max_len = max(len(item1), len(item2))
    return 1 - dist / max_len if max_len > 0 else 0.0


def preprocesssing(text: str):
    """Нормализация текста:
    преобразование всех символов в нижний регистр, замена синонимов, удаление второстепенных слов,
    удаление лишних пробелов"""
    text = text.lower()
    words = text.split()
    words = [synonyms.get(word, word) for word in words]
    text = " ".join(words)
    text = " ".join(text.split())

    return text


if __name__ == "__main__":

    new_items = []
    """Читаем файл new_items.txt с помощью контекстного менеджера.
    Нормализуем текст информации о товарах в перечне новых товарных предложений.
    Добавляем в new_items."""
    try:
        with open(file="new_items.txt", mode="r", encoding="UTF-8") as new_items_file:
            for line in new_items_file:
                line = line.strip()
                if not line:
                    continue
                if SIMILARITY_THRESHOLD:
                    line = preprocesssing(line)
                new_items.append(preprocesssing(line))
    except FileNotFoundError as e:
        print(f"Error! File not found!")

    duplicates = []

    """Читаем файл catalog.txt с помощью контекстного менеджера.
        Нормализуем текст информации о товаре в каталоге товаров.
        Находим дубликаты новых товарных предложений с товарами из каталога
        с помощью вышеуказанных функций.
        Добавляем в duplicates в соответствии с требованиями описания выходных данных."""
    try:
        with open(file="catalog.txt", mode="r", encoding="UTF-8") as catalog_file:
            for line in catalog_file:
                line = line.strip()
                if SIMILARITY_THRESHOLD:
                    line = preprocesssing(line)
                for item in new_items:
                    similarity_score = similarity(item, line)
                    if similarity_score >= SIMILARITY_THRESHOLD:
                        duplicates.append(
                            {
                                item[: item.find(" ")]: [
                                    {
                                        "catalog_id": line[: line.find(" ")],
                                        "similarity_score": round(similarity_score, 2),
                                    }
                                ]
                            }
                        )
    except FileNotFoundError as e:
        print(f"Error! File not found!")

    result = {}

    for duplicate in duplicates:
        result.update(duplicate)

    """Записываем результат в JSON, где для каждого нового товара приведён список 
    найденных дубликатов из каталога с указанием коэффициента схожести."""
    with open("duplicates.json", "w", encoding="utf-8") as result_file:
        json.dump(result, result_file, ensure_ascii=False, indent=4)
