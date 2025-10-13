file_text = open(file="text_file.txt", mode="r", encoding="UTF-8")
res = 0
for line in file_text:
    res += len(line.replace('.', '').replace('—', '').strip().split())
print(res)