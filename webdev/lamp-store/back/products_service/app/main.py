from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.v1.router import api_router

app = FastAPI(title="Lamp Store — products_service")

register_error_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
