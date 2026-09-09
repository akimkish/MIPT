"""Тесты HTTP-эндпоинтов заказов и /health (сценарии 44-56).

Авторизация в этих тестах проверяется через claim "permissions"
(RS256-токены), а не через роли — orders_service не знает о ролях
admin_service и сравнивает только строки прав (см. auth_contract в
INTEGRATION_CONTRACT.md и app/core/security.py).
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.permissions import Permission
from app.models.enums import OrderStatus
from tests.conftest import make_order


@pytest.mark.asyncio
async def test_list_orders_happy_path(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """44. GET /orders с валидным токеном — 200, тело — PaginatedResponse."""
    db_session.add(make_order())
    await db_session.flush()

    response = await client.get("/api/v1/orders", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert "items" in body and "total" in body
    assert body["total"] == 1


@pytest.mark.asyncio
async def test_list_orders_filters_by_status(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """45. GET /orders?status=paid возвращает только заказы в статусе paid."""
    db_session.add(make_order(status=OrderStatus.PAID.value))
    db_session.add(make_order(status=OrderStatus.NEW.value))
    await db_session.flush()

    response = await client.get(
        "/api/v1/orders",
        params={"status": "paid"},
        headers=auth_headers(),
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "paid"


@pytest.mark.asyncio
async def test_list_orders_email_filter_is_case_insensitive_end_to_end(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """46. Сквозная проверка нормализации email от API до репозитория."""
    db_session.add(make_order(email="buyer@example.com"))
    await db_session.flush()

    response = await client.get(
        "/api/v1/orders",
        params={"email": "BUYER@EXAMPLE.COM"},
        headers=auth_headers(),
    )

    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_view_only_permission_cannot_manage(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """47. Только VIEW_ORDERS: GET /orders — 200, PATCH .../status — 403.

    Заменяет прежнюю формулировку "роль moderator": orders_service не
    смотрит на роль, только на claim "permissions" — поэтому сценарий
    "недостаточно прав на управление" здесь выражается как токен без
    MANAGE_ORDERS, а не как конкретная роль admin_service.
    """
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()

    view_only = auth_headers(permissions=[Permission.VIEW_ORDERS])

    list_response = await client.get("/api/v1/orders", headers=view_only)
    assert list_response.status_code == 200

    patch_response = await client.patch(
        f"/api/v1/orders/{order.order_id}/status",
        json={"status": "paid"},
        headers=view_only,
    )
    assert patch_response.status_code == 403


@pytest.mark.asyncio
async def test_get_order_returns_items(
    client: AsyncClient, saved_order, auth_headers
) -> None:
    """48. GET /orders/{id} — 200, в теле присутствуют items."""
    response = await client.get(
        f"/api/v1/orders/{saved_order.order_id}", headers=auth_headers()
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_get_order_not_found_is_404(client: AsyncClient, auth_headers) -> None:
    """49. GET /orders/{id} для несуществующего заказа — 404 с телом detail."""
    response = await client.get(
        f"/api/v1/orders/{uuid.uuid4()}", headers=auth_headers()
    )

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_order_invalid_uuid_is_422(client: AsyncClient, auth_headers) -> None:
    """50. Невалидный UUID в пути — 422 (валидация FastAPI до сервиса)."""
    response = await client.get(
        "/api/v1/orders/not-a-uuid", headers=auth_headers()
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_status_happy_path(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """51. PATCH .../status с допустимым переходом и правом MANAGE_ORDERS — 200."""
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/orders/{order.order_id}/status",
        json={"status": "paid"},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_update_status_invalid_transition_is_409(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """52. Недопустимый переход — 409 с телом detail."""
    order = make_order(status=OrderStatus.COMPLETED.value)
    db_session.add(order)
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/orders/{order.order_id}/status",
        json={"status": "new"},
        headers=auth_headers(),
    )

    assert response.status_code == 409
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_update_status_unknown_value_is_422(
    client: AsyncClient, db_session, auth_headers
) -> None:
    """53. Значение статуса вне OrderStatus — 422 на уровне схемы, сервис не вызывается."""
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/orders/{order.order_id}/status",
        json={"status": "delivered"},
        headers=auth_headers(),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_status_missing_order_is_404(
    client: AsyncClient, auth_headers
) -> None:
    """54. PATCH .../status для несуществующего заказа — 404."""
    response = await client.patch(
        f"/api/v1/orders/{uuid.uuid4()}/status",
        json={"status": "paid"},
        headers=auth_headers(),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_status_without_token_is_401(
    client: AsyncClient, db_session
) -> None:
    """55. Edge-case: PATCH без токена — 401, до какой-либо валидации тела."""
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/orders/{order.order_id}/status",
        json={"status": "not-even-a-real-status"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_check_does_not_touch_db(client: AsyncClient) -> None:
    """56. GET /health — 200 без токена и без обращения к БД."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}