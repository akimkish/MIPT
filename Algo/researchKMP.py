from typing import List

def prefix_function(s: str) -> List[int]:
    n = len(s)
    pi = [0] * n
    k = 0
    for i in range(1, n):
        while k > 0 and s[k] != s[i]:
            k = pi[k - 1]
        if s[k] == s[i]:
            k += 1
        pi[i] = k
    return pi

def levenshtein_distance(s1: str, s2: str) -> int:
    n = len(s1) + 1
    m = len(s2) + 1
    dp = [[0] * m for _ in range(n)]
    for i in range(n):
        dp[i][0] = i
    for j in range(m):
        dp[0][j] = j
    for i in range(1, n):
        for j in range(1, m):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min([
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost
                ])
    return dp[n-1][m-1]

words = [w.strip(".,!?") for w in input().strip().lower().split() if w]
lim = int(input())

data = []
for idx, word in enumerate(words):
    if len(word) > 0:
        pi = prefix_function(word)
        sum_pi = sum(pi)
        data.append((sum_pi, len(word), -idx, word))

res_data = max(data)
res_word = res_data[3]
res_sum_pi = res_data[0]

count = 0
for word in words:
    if word != res_word and levenshtein_distance(word, res_word) <= lim:
        count += 1

print(data)
print(res_word)
print(res_sum_pi)
print(count)