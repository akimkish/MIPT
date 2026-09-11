import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo import Promo


class PromoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, promo_id: uuid.UUID) -> Promo | None:
        """Возвращает акцию по идентификатору.

        Args:
            promo_id: Идентификатор акции.

        Returns:
            Акцию или `None`, если она не найдена.
        """
        return await self._session.get(Promo, promo_id)

    async def list_active_for_product(
        self, product_id: uuid.UUID, at: datetime
    ) -> Sequence[Promo]:
        """Возвращает акции товара, действующие в указанный момент.

        Args:
            product_id: Идентификатор товара.
            at: Момент времени, на который проверяется действие акции
                (передаётся сервисом явно, чтобы расчёт был воспроизводим
                и тестируем без подмены системного времени).

        Returns:
            Список подходящих акций; пустой список, если акций нет.
        """
        stmt = select(Promo).where(
            Promo.product_id == product_id,
            Promo.is_active.is_(True),
            Promo.valid_from <= at,
            Promo.valid_to >= at,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_active_for_products(
        self, product_ids: Sequence[uuid.UUID], at: datetime
    ) -> Sequence[Promo]:
        """Возвращает действующие акции сразу для списка товаров.

        Args:
            product_ids: Идентификаторы товаров.
            at: Момент времени, на который проверяется действие акций.

        Returns:
            Список акций по всем переданным товарам вперемешку —
            группировку по `product_id` делает сервисный слой.
        """
        if not product_ids:
            return []
        stmt = select(Promo).where(
            Promo.product_id.in_(product_ids),
            Promo.is_active.is_(True),
            Promo.valid_from <= at,
            Promo.valid_to >= at,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_product(
        self,
        product_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Promo], int]:
        """Возвращает страницу всех акций товара, включая неактивные.

        Args:
            product_id: Идентификатор товара.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка акций и общего их количества.
        """
        conditions = [Promo.product_id == product_id]

        items_stmt = (
            select(Promo)
            .where(*conditions)
            .order_by(Promo.valid_from.desc())
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Promo).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def create(self, promo: Promo) -> Promo:
        """Добавляет акцию в сессию.

        Args:
            promo: Заполненный ORM-объект акции.

        Returns:
            Тот же объект с заполненными временными метками.
        """
        self._session.add(promo)
        await self._session.flush()
        await self._session.refresh(promo)
        return promo

    async def update(self, promo: Promo, values: dict[str, object]) -> Promo:
        """Применяет к акции набор изменённых полей.

        Args:
            promo: Существующий ORM-объект акции.
            values: Словарь «поле → новое значение».

        Returns:
            Обновлённый ORM-объект акции.
        """
        for field, value in values.items():
            setattr(promo, field, value)
        await self._session.flush()
        await self._session.refresh(promo)
        return promo
