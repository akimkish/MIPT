"""FastAPI-зависимости слоя api: сессия БД и сборка сервисов."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.services.order import OrderService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает асинхронную сессию БД на время запроса.

    Явное закрытие через `async with` гарантирует возврат соединения
    в пул даже при исключении внутри роута — сервисы сами вызывают
    `commit`, здесь только жизненный цикл сессии.

    Yields:
        Открытая сессия SQLAlchemy.
    """
    async with async_session_factory() as session:
        yield session


async def get_order_service(
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    """Собирает `OrderService` с сессией текущего запроса.

    Args:
        session: Сессия БД, полученная через `get_session`.

    Returns:
        Готовый к использованию сервис заказов.
    """
    return OrderService(session)