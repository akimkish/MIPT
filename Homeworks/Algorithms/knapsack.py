W = int(input())
n = int(input())
weights = list(map(int, input().split()))

dp = [0] * (W + 1)

for i in range(n):
    current_weight = weights[i]
    for w in range(W, current_weight - 1, -1):
        dp[w] = max(dp[w], dp[w - current_weight] + current_weight)

print(dp[W])