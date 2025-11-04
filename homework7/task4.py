import requests
from typing import NoReturn

class BadRequest(Exception):
    pass

class NotFound(Exception):
    pass

class HttpError(Exception):
    pass

def post_data(url: str = "https://jsonplaceholder.typicode.com/posts") -> NoReturn:
    data_to_post = {"userId": 21, "id": 101, "title": "It's title of post", 'body': "It's body of post"}
    response = requests.post(url, json=data_to_post)
    if response.status_code == 201:
        data = response.json()
        print(f"Id of post: {data["id"]}\nTitle of post: {data["title"]}\nBody of post: {data["body"]}")
    elif response.status_code == 400:
        raise BadRequest
    elif response.status_code == 404:
        raise NotFound
    else:
        raise HttpError

if __name__ == "__main__":
    try:
        post_data()
    except BadRequest:
        print(f"Error! Code 400")
    except NotFound:
        print(f"Error! Code 404")
    except HttpError:
        print(f"Error!")