class EvenNumber(Exception):
    pass

class NegativeNumber(Exception):
    pass

def sum_posi_odd_nums(nums):
    sum = 0
    for num in nums:
        if num % 2 == 0:
            raise EvenNumber(f"{num} - четное число!")
        if num < 0:
            raise NegativeNumber(f"{num} - отрицательное число!")
        sum += num
    return sum

mass = map(int, input().split())
try:
    res = sum_posi_odd_nums(mass)
except EvenNumber as er:
    print(f"Ошибка: {er}")
except NegativeNumber as er:
    print(f"Ошибка: {er}")
else:
    print(res)