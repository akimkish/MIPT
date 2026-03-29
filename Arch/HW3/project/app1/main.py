from fastapi import FastAPI

app = FastAPI()


@app.get("/api/v1")
async def get_data():
    return {"message": "App1"}
