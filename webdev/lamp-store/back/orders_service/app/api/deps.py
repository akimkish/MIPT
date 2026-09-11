from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.services.order import OrderService


async def get_session() -> AsyncGenerator[AsyncSession, None]:

    async with async_session_factory() as session:
        yield session


async def get_order_service(
    session: AsyncSession = Depends(get_session),
) -> OrderService:

    return OrderService(session)