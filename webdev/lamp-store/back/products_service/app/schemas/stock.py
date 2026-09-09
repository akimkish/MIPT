"""Схемы service-to-service контракта резервирования остатка.

Соответствуют эндпоинтам `api/v1/internal.py`, которые пока никем не
вызываются (orders_service ещё не реализован) — это заготовка контракта
на будущее, аутентификация service-token описана в INTEGRATION_CONTRACT.md
и в эти схемы не входит.
"""

import uuid

from pydantic import BaseModel, Field


class StockItem(BaseModel):
    """Одна позиция в запросе на резервирование остатка.

    Attributes:
        product_id: Идентификатор товара.
        quantity: Списываемое количество, > 0.
    """

    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)


class StockReserveRequest(BaseModel):
    """Запрос на атомарное списание остатка по всем позициям заказа.

    Attributes:
        order_id: Идентификатор заказа из orders_service (используется
            как часть первичного ключа идемпотентности в `stock_operations`).
        items: Позиции заказа для списания. Все списываются в одной
            транзакции products_service (см. domain_decisions).
    """

    order_id: uuid.UUID
    items: list[StockItem] = Field(..., min_length=1)


class StockReleaseRequest(BaseModel):
    """Запрос на возврат ранее списанного остатка по заказу.

    Attributes:
        order_id: Идентификатор заказа, для которого нужно выполнить
            возврат. Сами позиции сервис берёт из `payload` строки
            `reserve` в `stock_operations` — они не передаются повторно,
            чтобы вызывающая сторона не могла случайно вернуть не то
            количество, что было списано.
    """

    order_id: uuid.UUID


class StockOperationResult(BaseModel):
    """Результат операции резервирования/возврата остатка.

    Attributes:
        order_id: Идентификатор заказа.
        operation: Выполненная операция (`reserve` или `release`).
        already_applied: `True`, если операция с таким `order_id` уже
            была применена ранее и повторный вызов — идемпотентный
            no-op (например, ретрай orders_service после таймаута).
    """

    order_id: uuid.UUID
    operation: str
    already_applied: bool
