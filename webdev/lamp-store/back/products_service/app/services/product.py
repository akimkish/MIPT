"""Бизнес-логика управления товарами (административная часть).

Чтение витрины живёт в `catalog.py`; здесь — создание, изменение
и деактивация товаров, то есть операции для админов.
"""
from typing import Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.category import CategoryRepository
from app.repositories.manufacturer import ManufacturerRepository
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.exceptions import ConflictError, NotFoundError


class ProductService:
    """Сценарии управления карточками товаров."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._repository = ProductRepository(session)
        self._categories = CategoryRepository(session)
        self._manufacturers = ManufacturerRepository(session)

    async def get(self, product_id: uuid.UUID) -> Product:
        """Возвращает товар по идентификатору без фильтра активности.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Найденный товар.

        Raises:
            NotFoundError: Если товар не найден.
        """
        product = await self._repository.get_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Товар {product_id} не найден")
        return product

    async def create(self, data: ProductCreate) -> Product:
        """Создаёт товар.

        Существование категории и производителя проверяется явно, до
        вставки: иначе пользователь получил бы ошибку внешнего ключа
        от БД вместо понятного сообщения.

        Args:
            data: Данные нового товара.

        Returns:
            Созданный товар.

        Raises:
            NotFoundError: Если категория или производитель не найдены.
            ConflictError: Если артикул уже занят.
        """
        await self._ensure_references(data.category_id, data.manufacturer_id)

        if await self._repository.get_by_sku(data.sku) is not None:
            raise ConflictError(f"Товар с артикулом «{data.sku}» уже существует")

        product = Product(**data.model_dump())
        await self._repository.create(product)
        await self._session.commit()
        return product

    async def update(self, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        """Обновляет товар.

        Остаток (`quantity`) этим методом не меняется — он отсутствует
        в схеме `ProductUpdate` и управляется только `StockService`.

        Args:
            product_id: Идентификатор товара.
            data: Изменяемые поля.

        Returns:
            Обновлённый товар.

        Raises:
            NotFoundError: Если товар, категория или производитель
                не найдены.
            ConflictError: Если новый артикул занят другим товаром.
        """
        product = await self.get(product_id)
        values = data.model_dump(exclude_unset=True)

        await self._ensure_references(
            values.get("category_id"), values.get("manufacturer_id")
        )

        new_sku = values.get("sku")
        if new_sku is not None:
            existing = await self._repository.get_by_sku(new_sku)
            if existing is not None and existing.product_id != product_id:
                raise ConflictError(f"Артикул «{new_sku}» уже занят")

        await self._repository.update(product, values)
        await self._session.commit()
        return product

    async def deactivate(self, product_id: uuid.UUID) -> Product:
        """Снимает товар с витрины.

        Физическое удаление товаров запрещено: на них ссылаются отзывы,
        акции и позиции заказов в orders_service.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Деактивированный товар.

        Raises:
            NotFoundError: Если товар не найден.
        """
        product = await self.get(product_id)
        await self._repository.update(product, {"is_active": False})
        await self._session.commit()
        return product

    async def _ensure_references(
        self,
        category_id: uuid.UUID | None,
        manufacturer_id: uuid.UUID | None,
    ) -> None:
        """Проверяет существование указанных категории и производителя.

        Args:
            category_id: Идентификатор категории или `None`, если поле
                не передавалось.
            manufacturer_id: Идентификатор производителя или `None`.

        Raises:
            NotFoundError: Если указанная сущность не найдена.
        """
        if category_id is not None:
            if await self._categories.get_by_id(category_id) is None:
                raise NotFoundError(f"Категория {category_id} не найдена")
        if manufacturer_id is not None:
            if await self._manufacturers.get_by_id(manufacturer_id) is None:
                raise NotFoundError(f"Производитель {manufacturer_id} не найден")

    async def list_products(
        self, *, only_active: bool = False, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Product], int]:
        """Возвращает страницу товаров для админской панели.

        В отличие от `CatalogService.list_catalog`, не считает цены с
        учётом акций и по умолчанию показывает и неактивные товары —
        админу нужно видеть скрытые с витрины позиции, чтобы их включить.

        Args:
            only_active: Ограничить выборку активными товарами.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка товаров и их общего количества.
        """
        return await self._repository.list_products(
            only_active=only_active, limit=limit, offset=offset
        )
