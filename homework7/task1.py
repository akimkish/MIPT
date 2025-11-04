import requests
from typing import NoReturn

def get_and_fetch(url: str = "https://jsonplaceholder.typicode.com/posts") -> NoReturn:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for post in data[:5]:
            print(f"Title: {post["title"]}")
            print(f"Body: {post["body"]}\n")
    else:
        print(f"Code {response.status_code}")       

if __name__ == "__main__":
    get_and_fetch()