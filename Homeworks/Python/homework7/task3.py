import requests
from typing import NoReturn


def post_data(url: str = "https://jsonplaceholder.typicode.com/posts") -> NoReturn:
    data_to_post = {"userId": 21, "id": 101, "title": "It's title of post", 'body': "It's body of post"}
    response = requests.post(url, json=data_to_post)
    if response.status_code == 201:
        data = response.json()
        print(f"Id of post: {data["id"]}\nTitle of post: {data["title"]}\nBody of post: {data["body"]}")
    else:
        print(f"Code {response.status_code}")

if __name__ == "__main__":
    post_data()