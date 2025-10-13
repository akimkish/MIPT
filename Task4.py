file_input = open(file="input.txt", mode="r", encoding="UTF-8")
unique_str = set()

for line in file_input:
    unique_str.add(line.strip())

with open(file="unique_output.txt", mode="w", encoding="UTF-8") as unique_output:
    for line in unique_str:
        unique_output.write(f"{line}\n")
