x, y = input(), input()
try:
    res = int(x) / int(y)
except ZeroDivisionError as er0:
    print(f"Ошибка {er0} - деление на 0.")
except ValueError as erv:
    print(f"Ошибка {erv} - некорректное значение.") 
else:
    print(res)