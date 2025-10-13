file_source = open(file="source.txt", mode="r", encoding="UTF-8")
with open(file="destination.txt", mode="w", encoding="UTF-8") as new_file:
    for line in file_source:
        new_file.write(line) 
