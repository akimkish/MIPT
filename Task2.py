file_prices = open(file="prices.txt", mode="r", encoding="UTF-8")
final_price = 0
for line in file_prices:
    final_price += int(line.split()[1]) * int(line.split()[2])
print(final_price)