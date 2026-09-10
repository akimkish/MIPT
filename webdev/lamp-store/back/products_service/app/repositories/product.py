import uuid
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.enums import SocketType
from app.models.manufacturer import Manufacturer
from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        """Возвращает товар по идентификатору без связанных сущностей.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Товар или `None`, если он не найден.
        """
        return await self._session.get(Product, product_id)

    async def get_by_id_with_relations(self, product_id: uuid.UUID) -> Product | None:
        """Возвращает товар вместе с категорией и производителем.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Товар с загруженными связями или None.
        """
        stmt = (
            select(Product)
            .where(Product.product_id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.manufacturer),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        """Возвращает товар по артикулу.

        Args:
            sku: Артикул товара.

        Returns:
            Товар или None, если он не найден.
        """
        stmt = select(Product).where(Product.sku == sku)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_ids(
        self, product_ids: Sequence[uuid.UUID]
    ) -> Sequence[Product]:
        """Возвращает товары по списку идентификаторов

        Args:
            product_ids: Идентификаторы искомых товаров.

        Returns:
            Найденные товары. Отсутствующие идентификаторы просто не
            попадают в результат — сверку полноты делает сервисный слой.
        """
        if not product_ids:
            return []
        stmt = select(Product).where(Product.product_id.in_(product_ids))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    def _catalog_conditions(
        self,
        *,
        only_active: bool,
        category_id: uuid.UUID | None,
        manufacturer_id: uuid.UUID | None,
        socket_type: SocketType | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        search: str | None,
        in_stock_only: bool,
    ) -> list[ColumnElement[bool]]:
        """Собирает список условий WHERE для выборки товаров витрины.

        Args:
            only_active: Учитывать `is_active` товара, категории и бренда.
            category_id: Фильтр по категории.
            manufacturer_id: Фильтр по производителю.
            socket_type: Фильтр по типу цоколя.
            min_price: Нижняя граница цены включительно.
            max_price: Верхняя граница цены включительно.
            search: Подстрока для поиска по названию (без учёта регистра).
            in_stock_only: Возвращать только товары с `quantity > 0`.

        Returns:
            Список условий для передачи в `.where(*conditions)`.
        """
        conditions: list[ColumnElement[bool]] = []

        if only_active:
            # Витрина скрывает товар, если выключен он сам либо его
            # категория/производитель — все три флага в одном месте.
            conditions.extend(
                [
                    Product.is_active.is_(True),
                    Category.is_active.is_(True),
                    Manufacturer.is_active.is_(True),
                ]
            )
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if manufacturer_id is not None:
            conditions.append(Product.manufacturer_id == manufacturer_id)
        if socket_type is not None:
            conditions.append(Product.socket_type == socket_type.value)
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if search:
            conditions.append(Product.product_name.ilike(f"%{search}%"))
        if in_stock_only:
            conditions.append(Product.quantity > 0)

        return conditions

    async def list_products(
        self,
        *,
        only_active: bool = True,
        category_id: uuid.UUID | None = None,
        manufacturer_id: uuid.UUID | None = None,
        socket_type: SocketType | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
        in_stock_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Product], int]:
        """Возвращает страницу товаров витрины и общее их количество.

        Args:
            only_active: Применять фильтр активности (товар, категория,
                производитель). Для админских списков передаётся `False`.
            category_id: Фильтр по категории.
            manufacturer_id: Фильтр по производителю.
            socket_type: Фильтр по типу цоколя.
            min_price: Нижняя граница цены включительно.
            max_price: Верхняя граница цены включительно.
            search: Подстрока для поиска по названию товара.
            in_stock_only: Возвращать только товары в наличии.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка товаров (с загруженными категорией и
            производителем) и общего количества подходящих записей.
        """
        conditions = self._catalog_conditions(
            only_active=only_active,
            category_id=category_id,
            manufacturer_id=manufacturer_id,
            socket_type=socket_type,
            min_price=min_price,
            max_price=max_price,
            search=search,
            in_stock_only=in_stock_only,
        )

        items_stmt = (
            select(Product)
            .join(Product.category)
            .join(Product.manufacturer)
            .where(*conditions)
            .options(
                selectinload(Product.category),
                selectinload(Product.manufacturer),
            )
            .order_by(Product.created_at.desc(), Product.product_id)
            .limit(limit)
            .offset(offset)
        )
        total_stmt = (
            select(func.count())
            .select_from(Product)
            .join(Product.category)
            .join(Product.manufacturer)
            .where(*conditions)
        )

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def create(self, product: Product) -> Product:
        """Добавляет товар в сессию.

        Args:
            product: Заполненный ORM-объект товара.

        Returns:
            Тот же объект с заполненными временными метками.
        """
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def update(self, product: Product, values: dict[str, object]) -> Product:
        """Применяет к товару набор изменённых полей.

         Args:
            product: Существующий ORM-объект товара.
            values: Словарь «поле → новое значение».

        Returns:
            Обновлённый ORM-объект товара.
        """
        for field, value in values.items():
            setattr(product, field, value)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def decrease_quantity(self, product_id: uuid.UUID, quantity: int) -> bool:
        """Атомарно списывает остаток товара, если его достаточно.

        Args:
            product_id: Идентификатор товара.
            quantity: Списываемое количество, должно быть > 0.

        Returns:
            `True`, если строка обновлена (остатка хватило);
            `False`, если товара нет либо остаток меньше требуемого.
        """
        stmt = (
            update(Product)
            .where(
                Product.product_id == product_id,
                Product.quantity >= quantity,
            )
            .values(quantity=Product.quantity - quantity)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount == 1

    async def increase_quantity(self, product_id: uuid.UUID, quantity: int) -> bool:
        """Атомарно возвращает остаток товара на склад.

        Args:
            product_id: Идентификатор товара.
            quantity: Возвращаемое количество, должно быть > 0.

        Returns:
            `True`, если строка обновлена; `False`, если товар не найден.
        """
        stmt = (
            update(Product)
            .where(Product.product_id == product_id)
            .values(quantity=Product.quantity + quantity)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount == 1
