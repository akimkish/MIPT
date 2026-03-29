from fastapi import FastAPI
import requests
from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    internal_host: str = os.getenv("APP1_HOST", "app1")
    internal_port: int = os.getenv("APP1_PORT", 8000)

settings = Settings()

app = FastAPI()

@app.get("/api/v1")
async def get_data():
    try:
        internal_url = f"http://{settings.internal_host}:{settings.internal_port}/api/v1"
        response = requests.get(internal_url)
        response.raise_for_status() 
        data = response.json()
        external_response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
        external_response.raise_for_status()
        external_data = external_response.json()
        return {"meassage": "App2", "internal_data": data, "external_data": external_data}
    except requests.exceptions.RequestException as e:
        return {"error": e}

