import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DiscountType
from app.models.promo import Promo
from app.repositories.product import ProductRepository
from app.repositories.promo import PromoRepository
from app.schemas.promo import PromoCreate, PromoUpdate
from app.services.exceptions import DomainValidationError, NotFoundError


class PromoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = PromoRepository(session)
        self._products = ProductRepository(session)

    async def get(self, promo_id: uuid.UUID) -> Promo:
        """Возвращает акцию по идентификатору.

        Args:
            promo_id: Идентификатор акции.

        Returns:
            Найденную акцию.

        """
        promo = await self._repository.get_by_id(promo_id)
        if promo is None:
            raise NotFoundError(f"Акция {promo_id} не найдена")
        return promo

    async def list_for_product(
        self, product_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Promo], int]:
        """Возвращает все акции товара, включая выключенные и просроченные.

        Args:
            product_id: Идентификатор товара.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка акций и их общего количества.
        """
        if await self._products.get_by_id(product_id) is None:
            raise NotFoundError(f"Товар {product_id} не найден")

        return await self._repository.list_by_product(
            product_id, limit=limit, offset=offset
        )

    async def create(self, data: PromoCreate) -> Promo:
        """Создаёт акцию на товар.

        Args:
            data: Данные новой акции.

        Returns:
            Созданную акцию.

        """
        if await self._products.get_by_id(data.product_id) is None:
            raise NotFoundError(f"Товар {data.product_id} не найден")

        promo = Promo(**data.model_dump())
        await self._repository.create(promo)
        await self._session.commit()
        return promo

    async def update(self, promo_id: uuid.UUID, data: PromoUpdate) -> Promo:
        """Обновляет акцию с проверкой согласованности полей.

             Args:
            promo_id: Идентификатор акции.
            data: Изменяемые поля.

        Returns:
            Обновлённую акцию.

        """
        promo = await self.get(promo_id)
        values = data.model_dump(exclude_unset=True)

        self._validate_merged(
            discount_type=values.get("discount_type", promo.discount_type),
            discount=values.get("discount", promo.discount),
            valid_from=values.get("valid_from", promo.valid_from),
            valid_to=values.get("valid_to", promo.valid_to),
        )

        await self._repository.update(promo, values)
        await self._session.commit()
        return promo

    async def deactivate(self, promo_id: uuid.UUID) -> Promo:
        """Выключает акцию.

        Args:
            promo_id: Идентификатор акции.

        Returns:
            Выключенную акцию.

        """
        promo = await self.get(promo_id)
        await self._repository.update(promo, {"is_active": False})
        await self._session.commit()
        return promo

    @staticmethod
    def _validate_merged(
        *,
        discount_type: str,
        discount: Decimal,
        valid_from: datetime,
        valid_to: datetime,
    ) -> None:
        """Проверяет итоговое состояние акции после слияния изменений.

        Args:
            discount_type: Тип скидки.
            discount: Величина скидки.
            valid_from: Начало действия акции.
            valid_to: Конец действия акции.

        """
        if discount_type == DiscountType.PERCENT and discount > 100:
            raise DomainValidationError("Процентная скидка не может превышать 100")
        if valid_from >= valid_to:
            raise DomainValidationError("valid_from должен быть раньше valid_to")
