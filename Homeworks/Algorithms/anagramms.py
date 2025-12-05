words = input().split()
anagramms_groups = {}

for word in words:
    key = "".join(sorted(list(word.lower())))
    if key not in anagramms_groups:
        anagramms_groups[key] = []
        anagramms_groups[key].append(word)
    else:
        anagramms_groups[key].append(word)

anagramms = []

for words in anagramms_groups.values():
    anagramms.append(sorted(words))

for anagramm in sorted(anagramms, key=lambda x: x[0]):
    print(*anagramm)


