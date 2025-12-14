instr = input()
try:
    print(float(instr))
except ValueError as erv:
    print(f"Ошибка {erv} - данную строку невозможно преобразоват в число.")