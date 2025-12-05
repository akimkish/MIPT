import requests
from typing import NoReturn


def get_weather(city: str) -> NoReturn:
    api_key = '6d9b3e680342b38710b3b69c3e413341'
    response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric')
    if response.status_code == 200:
        data = response.json()
        print(f"Current temperature in {city}: {data["main"]["temp"]} C\nDescription: {data["weather"][0]["description"]}")
    else:
        print(f"Code {response.status_code}")

if __name__ == "__main__":
    get_weather("Moscow")