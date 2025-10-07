try:
    import math
    num = float(input())
    try:
        res = math.sqrt(num)
        print(res)
    except ValueError as e:
        print(f"Ошибка: {e} - корень не может быть извлечен из отрицатльного числа.")
except ImportError as e:
    print(f"Ошибка: {e} - библиотека не установлена")