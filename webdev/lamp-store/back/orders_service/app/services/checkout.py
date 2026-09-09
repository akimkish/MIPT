# orders_service/app/services/checkout.py
"""Оформление заказа: оркестрация двух БД без брокера сообщений.

Порядок шагов — единственное, что удерживает согласованность:

    1. INSERT orders(status='pending') + COMMIT
       UNIQUE(idempotency_key) отсекает дубль ДО любого списания остатков.
       order_id из этого шага становится ключом идемпотентности для products.
    2. POST /internal/stock/prices — цены со скидками и снимок позиций.
       Остатки не трогает, поэтому сбой на этом шаге компенсации не требует.
       Заодно это единственная проверка is_active: сам reserve её не делает.
    3. POST /internal/stock/reserve — одна попытка, без ретраев.
    4. INSERT order_items из снимка + total_price + status='new' + COMMIT.

Компенсация (release) вызывается ТОЛЬКО там, где резерв мог состояться:
после неизвестного исхода шага 3 и после падения шага 4. При ConnectError
запрос не ушёл, компенсировать нечего — лишний release там безвреден,
но маскировал бы в логах реальную причину сбоя.

Известное упрощение: между шагами 2 и 3 акция может закончиться, и заказ
сохранится по цене, посчитанной на несколько миллисекунд раньше. В проде
цену фиксируют в той же транзакции, что и остаток; здесь цена и остаток
считаются двумя отдельными вызовами.

Ожидаемый интерфейс OrderRepository (repositories/order.py):
    create_pending(data) -> Order          # INSERT ... status='pending', COMMIT;
                                           # пробрасывает IntegrityError наверх
    get_by_idempotency_key(key) -> Order | None
    set_status(order_id, status) -> None   # UPDATE + COMMIT
    complete(order_id, lines) -> Order     # INSERT order_items, total_price,
                                           # status='new', один COMMIT
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.clients.exceptions import (
    InsufficientStockError,
    ProductNotAvailableError,
    ServiceRejectedError,
    ServiceUnavailableError,
    ServiceUnknownStateError,
)
from app.clients.products import ProductsClient
from app.clients.schemas import CartQuote, StockItemRequest
from app.models.enums import OrderStatus
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate
from app.services.exceptions import (
    CatalogItemUnavailableError,
    CheckoutUnavailableError,
    DuplicateOrderError,
    OutOfStockError,
)

logger = logging.getLogger(__name__)


class CheckoutService:
    """Сага оформления заказа."""

    def __init__(self, repository: OrderRepository, products: ProductsClient) -> None:
        """Инициализирует сервис.

        Args:
            repository: Репозиторий заказов orders_service.
            products: Клиент products_service (один на всё приложение).
        """
        self._repository = repository
        self._products = products

    async def create_order(self, payload: OrderCreate) -> Order:
        """Оформляет заказ целиком.

        Args:
            payload: Данные покупателя, позиции корзины и idempotency_key.

        Returns:
            Созданный заказ в статусе 'new' вместе с позициями.

        Raises:
            DuplicateOrderError: idempotency_key уже использован.
            OutOfStockError: Не хватает остатка.
            CatalogItemUnavailableError: Товар недоступен.
            CheckoutUnavailableError: products_service недоступен или сбойнул.
        """
        items = [
            StockItemRequest(product_id=item.product_id, quantity=item.quantity)
            for item in payload.items
        ]

        order = await self._create_pending(payload)
        quotes = await self._quote(order.order_id, items)
        await self._reserve(order.order_id, items)
        return await self._persist(order.order_id, items, quotes)

    # --- шаг 1 ---------------------------------------------------------------

    async def _create_pending(self, payload: OrderCreate) -> Order:
        """Создаёт заказ-заглушку в статусе 'pending'.

        Отдельный коммит нужен до похода в products_service: он фиксирует
        order_id (ключ идемпотентности) и через UNIQUE(idempotency_key)
        отсекает дубль формы раньше, чем будет списан остаток.

        Args:
            payload: Данные заказа.

        Returns:
            Сохранённый заказ в статусе 'pending'.

        Raises:
            DuplicateOrderError: Такой idempotency_key уже есть.
            CheckoutUnavailableError: Ошибка БД orders_service.
        """
        try:
            return await self._repository.create_pending(payload)
        except IntegrityError as exc:
            logger.info(
                "Duplicate idempotency_key=%s rejected", payload.idempotency_key
            )
            raise DuplicateOrderError() from exc
        except SQLAlchemyError as exc:
            logger.exception("Failed to create pending order: %s", exc)
            raise CheckoutUnavailableError() from exc

    # --- шаг 2 ---------------------------------------------------------------

    async def _quote(
        self, order_id: UUID, items: list[StockItemRequest]
    ) -> dict[UUID, CartQuote]:
        """Получает цены и снимок позиций до изменения остатков.

        Ни одна ветка не вызывает release: этот эндпоинт остатки не
        меняет, компенсировать нечего даже при таймауте.

        Args:
            order_id: Идентификатор заказа (для логов и смены статуса).
            items: Позиции заказа.

        Returns:
            Снимок по каждому товару.

        Raises:
            CatalogItemUnavailableError: Хотя бы один товар недоступен.
            CheckoutUnavailableError: Любая ошибка обращения к каталогу.
        """
        try:
            quotes = await self._products.get_prices(items)
        except (
            ServiceUnavailableError,
            ServiceUnknownStateError,
            ServiceRejectedError,
        ) as exc:
            logger.warning(
                "Price quote failed for order_id=%s (%s)", order_id, exc.reason
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        by_id = {quote.product_id: quote for quote in quotes}
        unavailable = [
            str(item.product_id)
            for item in items
            if item.product_id not in by_id or not by_id[item.product_id].is_available
        ]
        if unavailable:
            logger.info(
                "Order %s rejected: products unavailable %s", order_id, unavailable
            )
            await self._mark_failed(order_id)
            raise CatalogItemUnavailableError(details={"product_ids": unavailable})

        return by_id

    # --- шаг 3 ---------------------------------------------------------------

    async def _reserve(self, order_id: UUID, items: list[StockItemRequest]) -> None:
        """Списывает остатки в products_service.

        Каждая ветка except отвечает на один вопрос: состоялась ли
        транзакция в чужой БД. От ответа зависит, нужна ли компенсация.

        Args:
            order_id: Идентификатор заказа, он же ключ идемпотентности.
            items: Позиции заказа.

        Raises:
            OutOfStockError: 409 от products_service.
            CatalogItemUnavailableError: 404 от products_service.
            CheckoutUnavailableError: Всё остальное.
        """
        try:
            result = await self._products.reserve(order_id, items)

        except ServiceUnavailableError as exc:
            # Запрос не ушёл: резерва точно нет, компенсация не нужна.
            logger.warning(
                "Reserve not sent for order_id=%s (%s)", order_id, exc.reason
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        except ServiceUnknownStateError as exc:
            # Запрос ушёл, исход неизвестен: остаток мог быть списан.
            logger.error(
                "Reserve outcome unknown for order_id=%s (%s), compensating",
                order_id,
                exc.reason,
            )
            if await self._release_best_effort(order_id):
                await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        except InsufficientStockError as exc:
            await self._mark_failed(order_id)
            raise OutOfStockError(details=exc.details) from exc

        except ProductNotAvailableError as exc:
            await self._mark_failed(order_id)
            raise CatalogItemUnavailableError(details=exc.details) from exc

        except ServiceRejectedError as exc:
            # Прочие 4xx: 401 (неверный INTERNAL_API_KEY) или 422 (разъехались
            # схемы). Транзакции в products не было, компенсация не нужна,
            # но это баг конфигурации — уровень ERROR.
            logger.error(
                "Reserve rejected for order_id=%s: HTTP %s code=%s",
                order_id,
                exc.status_code,
                exc.code,
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        if result.already_applied:
            # order_id только что сгенерирован, повтора быть не может.
            # Скорее всего, коллизия UUID невозможна, а вот дубль запроса
            # от прокси — вполне: стоит увидеть это в логах.
            logger.warning(
                "Reserve for order_id=%s reported already_applied", order_id
            )

    # --- шаг 4 ---------------------------------------------------------------

    async def _persist(
        self,
        order_id: UUID,
        items: list[StockItemRequest],
        quotes: dict[UUID, CartQuote],
    ) -> Order:
        """Сохраняет позиции заказа и переводит его в статус 'new'.

        Args:
            order_id: Идентификатор заказа.
            items: Исходные позиции (источник количеств).
            quotes: Снимок из products_service (источник цен и названий).

        Returns:
            Заказ в статусе 'new'.

        Raises:
            CheckoutUnavailableError: Ошибка БД; остаток при этом уже
                списан, поэтому выполняется компенсация.
        """
        lines = self._build_lines(items, quotes)
        try:
            return await self._repository.complete(order_id, lines)
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to persist items for order_id=%s, compensating", order_id
            )
            if await self._release_best_effort(order_id):
                await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

    @staticmethod
    def _build_lines(
        items: list[StockItemRequest], quotes: dict[UUID, CartQuote]
    ) -> list[dict[str, object]]:
        """Склеивает количества из корзины с ценами из снимка.

        Полнота снимка уже проверена на шаге 2, поэтому обращение по
        ключу здесь безопасно.

        Args:
            items: Позиции корзины.
            quotes: Снимок из products_service.

        Returns:
            Данные для INSERT в order_items.
        """
        lines: list[dict[str, object]] = []
        for item in items:
            quote = quotes[item.product_id]
            unit_price: Decimal = quote.unit_price
            lines.append(
                {
                    "external_product_id": quote.product_id,
                    "product_name": quote.product_name,
                    "sku": quote.sku,
                    "image_url": quote.image_url,
                    "item_quantity": item.quantity,
                    "original_unit_price": quote.original_unit_price,
                    "unit_price": unit_price,
                    "promo_id": quote.promo_id,
                    # Округление уже выполнено в products_service на уровне
                    # unit_price; здесь только умножение, иначе копейки поедут.
                    "total_price": unit_price * item.quantity,
                }
            )
        return lines

    # --- компенсация ---------------------------------------------------------

    async def _release_best_effort(self, order_id: UUID) -> bool:
        """Пытается вернуть остатки. Одна попытка, исключения не пробрасывает.

        Ретраев нет намеренно: release идемпотентен, поэтому недошедшую
        компенсацию безопасно доделать вручную по логам и таблице
        stock_operations.

        Args:
            order_id: Идентификатор заказа.

        Returns:
            True, если компенсация прошла; False, если заказ остался
            в статусе 'pending' и требует ручного разбора.
        """
        try:
            await self._products.release(order_id)
        except Exception as exc:  # noqa: BLE001 - компенсация не должна падать
            logger.error(
                "MANUAL ACTION REQUIRED: release failed for order_id=%s (%s), "
                "order left in 'pending'",
                order_id,
                exc,
            )
            return False
        logger.info("Stock released for order_id=%s", order_id)
        return True

    async def _mark_failed(self, order_id: UUID) -> None:
        """Переводит заказ в 'failed' отдельной транзакцией.

        Ошибка здесь не пробрасывается: покупателю всё равно уйдёт ответ
        об отказе, а заказ останется 'pending' и попадёт в ручной разбор.

        Args:
            order_id: Идентификатор заказа.
        """
        try:
            await self._repository.set_status(order_id, OrderStatus.FAILED)
        except SQLAlchemyError as exc:
            logger.error("Failed to mark order_id=%s as failed: %s", order_id, exc)