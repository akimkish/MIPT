from collections.abc import AsyncGenerator
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.exceptions import register_exception_handlers

from contextlib import asynccontextmanager
from app.clients.products import ProductsClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Создаёт один httpx-клиент на всё время жизни приложения."""
    app.state.products_client = ProductsClient()
    try:
        yield
    finally:
        await app.state.products_client.aclose()


app = FastAPI(title="Lamp Store — Orders Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
