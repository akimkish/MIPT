regions_data = {}
all_countries = []

with open(file="input.txt", mode="r", encoding="UTF-8") as input_file:
    next(input_file)
    for line in input_file:
        cur_line = line.strip().split(";")
        if float(cur_line[-1]) > 90.0:
            regions_data[cur_line[1]] = regions_data.get(cur_line[1], 0) + 1
        all_countries.append(cur_line[1])

leading_countries = []    

for region in regions_data:
    regions_data[region] = regions_data[region] / all_countries.count(region)

for region, part in regions_data.items():
    if part == max(regions_data.values()):
       leading_countries.append(region)

with open(file="output.txt", mode="w", encoding="UTF-8") as output_file:
    for el in sorted(leading_countries):
        output_file.write(f"{el}\n")