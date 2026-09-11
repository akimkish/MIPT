import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DiscountType, SocketType
from app.models.product import Product
from app.models.promo import Promo
from app.repositories.product import ProductRepository
from app.repositories.promo import PromoRepository
from app.schemas.product import ProductCatalogItem, ProductWithRelations, ProductRead
from app.services.exceptions import NotFoundError

CENTS = Decimal("0.01")


class PriceQuote(NamedTuple):
    """Результат расчёта цены единицы товара.

    Attributes:
        unit_price: Итоговая цена за единицу с учётом лучшей акции,
            округлённая до копеек.
        promo_id: Акция, давшая эту цену, или `None`, если ни одна
            акция не применилась и цена равна базовой.
    """

    unit_price: Decimal
    promo_id: uuid.UUID | None


class CartQuote(NamedTuple):
    """Снимок позиции корзины: цена плюс данные для позиции заказа.

    Attributes:
        product_id: Идентификатор товара.
        is_available: Доступен ли товар для заказа.
        product_name: Название на момент расчёта.
        sku: Артикул на момент расчёта.
        image_url: Ссылка на изображение.
        quantity_available: Остаток на складе на момент расчёта.
        original_unit_price: Базовая цена без скидки.
        unit_price: Цена за единицу с учётом лучшей акции.
        promo_id: Применённая акция или `None`.
    """

    product_id: uuid.UUID
    is_available: bool
    product_name: str | None = None
    sku: str | None = None
    image_url: str | None = None
    quantity_available: int | None = None
    original_unit_price: Decimal | None = None
    unit_price: Decimal | None = None
    promo_id: uuid.UUID | None = None


def round_money(value: Decimal) -> Decimal:
    """Округляет денежную величину до двух знаков по правилу ROUND_HALF_UP.

    Банковское округление (`ROUND_HALF_EVEN`, принятое в `Decimal`
    по умолчанию) для розничных цен неинтуитивно: 2.345 превратилось бы
    в 2.34. Поэтому правило задано явно.

    Args:
        value: Исходная величина.

    Returns:
        Величину, округлённую до двух знаков после запятой.
    """
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_promo(base_price: Decimal, promo: Promo) -> Decimal:
    """Применяет одну акцию к базовой цене единицы товара.

    Фиксированная скидка обрезается снизу нулём: скидка в 100 рублей
    на товар за 80 даёт цену 0, а не отрицательное значение.

    Args:
        base_price: Базовая цена за единицу.
        promo: Применяемая акция.

    Returns:
        Цену за единицу с учётом акции, округлённую до копеек.
    """
    if promo.discount_type == DiscountType.PERCENT:
        discounted = base_price * (Decimal(1) - promo.discount / Decimal(100))
    else:
        discounted = base_price - promo.discount

    if discounted < 0:
        discounted = Decimal(0)
    return round_money(discounted)


def calculate_unit_price(
    base_price: Decimal, promos: Sequence[Promo], quantity: int
) -> PriceQuote:
    """Выбирает лучшую для покупателя цену среди применимых акций.

    Args:
        base_price: Базовая цена товара за единицу.
        promos: Акции-кандидаты, действующие на нужный момент времени.
        quantity: Заказываемое количество единиц товара.

    Returns:
        Итоговую цену за единицу и идентификатор применённой акции.
    """
    best_price = round_money(base_price)
    best_promo_id: uuid.UUID | None = None

    for promo in promos:
        if quantity < promo.min_quantity:
            continue
        candidate = apply_promo(base_price, promo)
        if candidate < best_price:
            best_price = candidate
            best_promo_id = promo.promo_id

    return PriceQuote(unit_price=best_price, promo_id=best_promo_id)


def calculate_total_price(unit_price: Decimal, quantity: int) -> Decimal:
    """Считает стоимость позиции по уже округлённой цене за единицу.

    Args:
        unit_price: Округлённая цена за единицу.
        quantity: Количество единиц.

    Returns:
        Стоимость позиции.
    """
    return round_money(unit_price * quantity)


def build_bulk_hint(promos: Sequence[Promo]) -> str | None:
    """Формирует подпись об оптовой скидке для карточки товара.

    Args:
        promos: Действующие акции товара.

    Returns:
        Текст вида «от 3 шт. дешевле» для самой доступной оптовой акции
        либо `None`, если акций с `min_quantity > 1` нет.
    """
    bulk_quantities = [p.min_quantity for p in promos if p.min_quantity > 1]
    if not bulk_quantities:
        return None
    return f"от {min(bulk_quantities)} шт. дешевле"


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:

        self._products = ProductRepository(session)
        self._promos = PromoRepository(session)

    async def list_catalog(
        self,
        *,
        category_id: uuid.UUID | None = None,
        manufacturer_id: uuid.UUID | None = None,
        socket_type: SocketType | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
        in_stock_only: bool = False,
        limit: int = 20,
        offset: int = 0,
        at: datetime | None = None,
    ) -> tuple[list[ProductCatalogItem], int]:
        """Возвращает страницу витрины с ценами, учитывающими акции.

        Args:
            category_id: Фильтр по категории.
            manufacturer_id: Фильтр по производителю.
            socket_type: Фильтр по типу цоколя.
            min_price: Нижняя граница базовой цены.
            max_price: Верхняя граница базовой цены.
            search: Подстрока для поиска по названию товара.
            in_stock_only: Показывать только товары в наличии.
            limit: Размер страницы.
            offset: Смещение от начала выборки.
            at: Момент времени для проверки действия акций. По умолчанию
                текущее время в UTC; параметр вынесен наружу, чтобы
                расчёт был воспроизводим в тестах.

        Returns:
            Кортеж из списка позиций витрины и общего количества товаров,
            подходящих под фильтры.
        """
        moment = at or datetime.now(UTC)

        products, total = await self._products.list_products(
            only_active=True,
            category_id=category_id,
            manufacturer_id=manufacturer_id,
            socket_type=socket_type,
            min_price=min_price,
            max_price=max_price,
            search=search,
            in_stock_only=in_stock_only,
            limit=limit,
            offset=offset,
        )
        if not products:
            return [], total

        promos_by_product = await self._load_promos(
            [p.product_id for p in products], moment
        )
        items = [
            self._to_catalog_item(product, promos_by_product[product.product_id])
            for product in products
        ]
        return items, total

    async def get_product_card(
        self, product_id: uuid.UUID, at: datetime | None = None
    ) -> tuple[ProductWithRelations, ProductCatalogItem]:
        """Возвращает карточку товара с развёрнутыми связями и ценой.

        Args:
            product_id: Идентификатор товара.
            at: Момент времени для проверки действия акций.

        Returns:
            Кортеж из подробного представления товара (с категорией и
            производителем) и его витринного представления с ценой.

        """
        moment = at or datetime.now(UTC)

        product = await self._products.get_by_id_with_relations(product_id)
        if (
            product is None
            or not product.is_active
            or not product.category.is_active
            or not product.manufacturer.is_active
        ):
            raise NotFoundError(f"Товар {product_id} не найден")

        promos = await self._promos.list_active_for_product(product_id, moment)
        return (
            ProductWithRelations.model_validate(product),
            self._to_catalog_item(product, list(promos)),
        )

    async def quote_cart(
        self, requested: dict[uuid.UUID, int], at: datetime | None = None
    ) -> list[CartQuote]:
        """Считает цены и собирает снимок для набора «товар → количество».


        Args:
            requested: Соответствие идентификатора товара количеству.
            at: Момент времени для проверки действия акций. По умолчанию
                текущее время в UTC; вынесен наружу ради тестов.

        Returns:
            По одной записи на каждый запрошенный товар, в том порядке,
            в котором товары перечислены в `requested`.
        """
        moment = at or datetime.now(UTC)
        product_ids = list(requested)

        products = await self._products.get_many_by_ids(product_ids)
        available = {p.product_id: p for p in products if p.is_active}
        promos_by_product = await self._load_promos(list(available), moment)

        quotes: list[CartQuote] = []
        for product_id, quantity in requested.items():
            product = available.get(product_id)
            if product is None:
                quotes.append(CartQuote(product_id=product_id, is_available=False))
                continue

            price = calculate_unit_price(
                product.price, promos_by_product[product_id], quantity
            )
            quotes.append(
                CartQuote(
                    product_id=product.product_id,
                    is_available=True,
                    product_name=product.product_name,
                    sku=product.sku,
                    image_url=product.image_url,
                    quantity_available=product.quantity,
                    original_unit_price=round_money(product.price),
                    unit_price=price.unit_price,
                    promo_id=price.promo_id,
                )
            )
        return quotes

    async def _load_promos(
        self, product_ids: Sequence[uuid.UUID], at: datetime
    ) -> dict[uuid.UUID, list[Promo]]:
        """Загружает действующие акции и группирует их по товарам.

        Args:
            product_ids: Идентификаторы товаров.
            at: Момент времени для проверки действия акций.

        Returns:
            Словарь «товар → список акций»; товары без акций тоже
            присутствуют в словаре с пустым списком.
        """
        promos = await self._promos.list_active_for_products(product_ids, at)

        grouped: dict[uuid.UUID, list[Promo]] = defaultdict(list)
        for promo in promos:
            grouped[promo.product_id].append(promo)
        for product_id in product_ids:
            grouped.setdefault(product_id, [])
        return grouped

    @staticmethod
    def _to_catalog_item(
        product: Product, promos: Sequence[Promo]
    ) -> ProductCatalogItem:
        """Собирает витринное представление товара с ценой и подсказкой.

        Args:
            product: ORM-объект товара.
            promos: Действующие акции этого товара.

        Returns:
            Позицию витрины с рассчитанной ценой за единицу при qty=1.
        """
        base = ProductRead.model_validate(product)
        item = ProductCatalogItem(
            **base.model_dump(),
            display_price=calculate_unit_price(
                product.price, promos, quantity=1
            ).unit_price,
            bulk_discount_hint=build_bulk_hint(promos),
        )
        return item
