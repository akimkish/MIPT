x, y = input(), input()
try:
    res = int(x) / int(y)
except ZeroDivisionError as er:
    print(f"Ошибка {er} - деление на 0.")
else:
    print(res)