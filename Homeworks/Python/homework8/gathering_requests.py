import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from datetime import date
import json
import re


class Request(BaseModel):
    first_name: str = Field(
        pattern=r"\b[А-ЯЁ][а-яё]*\b",
        description="Имя должно состоять только из кириллицы и начинятс с заглавной буквы.",
    )

    last_name: str = Field(
            pattern=r"\b[А-ЯЁ][а-яё]*\b",
            description="Фамилия должно состоять только из кириллицы и начинятс с заглавной буквы.",
        )
    date_of_birth: date

    phone_number: str = Field(
        pattern=r"^\+79\d{9}$",
        description="Номер телефона должен быть в формате +7XXXXXXXXXX",
    )

    email: EmailStr


app = FastAPI()

@app.post("/requests", status_code=201)
async def gathering_requests(request: Request):
    data = request.model_dump()
    with open(file="requests.json", mode="w", encoding="UTF-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    uvicorn.run("gathering_requests:app", host="0.0.0.0", port=8000, reload=True)