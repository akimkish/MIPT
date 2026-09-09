"""Тесты Pydantic-схем в изоляции от БД (сценарии 57-60)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreate, OrderItemCreate, OrderRead, OrderStatusUpdate
from app.schemas.order_item import OrderItemRead


def test_order_create_normalizes_email_case() -> None:
    """57. OrderCreate приводит email к нижнему регистру на уровне схемы."""
    data = OrderCreate(
        idempotency_key="idem-1",
        user_name="Иван",
        phone="+79990000000",
        email="Buyer@Example.COM",
        delivery_address="ул. Ленина, 1",
        items=[OrderItemCreate(external_product_id=uuid.uuid4(), item_quantity=1)],
    )
    assert data.email == "buyer@example.com"


def test_order_create_rejects_empty_items() -> None:
    """58. OrderCreate с пустым списком позиций отклоняется."""
    with pytest.raises(ValidationError):
        OrderCreate(
            idempotency_key="idem-1",
            user_name="Иван",
            phone="+79990000000",
            email="buyer@example.com",
            delivery_address="ул. Ленина, 1",
            items=[],
        )


def test_order_status_update_rejects_unknown_value() -> None:
    """59. OrderStatusUpdate со значением вне OrderStatus — ValidationError."""
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="delivered")


def test_order_read_serializes_nested_items_from_orm_object() -> None:
    """60. OrderRead.model_validate корректно читает вложенные items из ORM-like объекта.

    Настоящий ORM-объект здесь не нужен — model_validate с
    from_attributes=True работает с любым объектом, у которого есть
    одноимённые атрибуты, что и проверяется без похода в БД.
    """

    class _FakeItem:
        item_id = uuid.uuid4()
        external_product_id = uuid.uuid4()
        product_name = "Лампа E27 LED 10W"
        sku = "LMP-000001"
        image_url = None
        item_quantity = 2
        original_unit_price = Decimal("200.00")
        unit_price = Decimal("180.00")
        promo_id = None
        total_price = Decimal("360.00")
        created_at = datetime.now(timezone.utc)

    class _FakeOrder:
        order_id = uuid.uuid4()
        idempotency_key = "idem-1"
        user_name = "Иван"
        phone = "+79990000000"
        email = "buyer@example.com"
        delivery_address = "ул. Ленина, 1"
        total_price = Decimal("360.00")
        status = "new"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        items = [_FakeItem()]

    result = OrderRead.model_validate(_FakeOrder())

    assert len(result.items) == 1
    assert isinstance(result.items[0], OrderItemRead)
    assert result.items[0].sku == "LMP-000001"