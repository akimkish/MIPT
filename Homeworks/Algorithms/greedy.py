n = int(input())

areas = []
for _ in range(n):
    begin, end = (int(i) for i in input().split())
    areas.append((begin, end))

areas.sort(key=lambda x: (x[1], x[0]))

points = []
last_point = None

for begin, end in areas:
    if last_point is None or begin > last_point:
        last_point = end
        points.append(last_point)

print(len(points))