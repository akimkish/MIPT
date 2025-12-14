k = int(input())
mass = [i for i in range (1,21)]
try:
    print(mass[k])
except IndexError as eri:
    print(f"Ошибка {eri} - индекс выходит за пределы списка.")