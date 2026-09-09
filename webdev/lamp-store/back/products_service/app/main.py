"""Точка входа FastAPI-приложения products_service."""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.v1.router import api_router

app = FastAPI(title="Lamp Store — products_service")

register_error_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Проверка живости сервиса без обращения к БД.

    Отвечает 200 сразу после старта uvicorn, что для этого проекта
    равносильно готовности: entrypoint.sh запускает uvicorn только
    после успешного `wait_for_db` и применения миграций (см.
    domain_decisions в PROMPT_CONTEXT.md). Это единственный сигнал
    готовности, который использует CI при polling `/health`.

    Returns:
        Статус сервиса.
    """
    return {"status": "ok"}