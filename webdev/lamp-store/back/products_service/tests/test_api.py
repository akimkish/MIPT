"""Сквозные HTTP-тесты: роуты, пагинация на границах, диспетчеризация ошибок."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_product

pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_returns_200_without_db(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestProductsListing:
    async def test_list_products_empty_catalog(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/products")
        assert response.status_code == 200
        assert response.json()["items"] == []

    async def test_limit_boundary_values_accepted(self, client: AsyncClient) -> None:
        for limit in (1, 100):
            response = await client.get("/api/v1/products", params={"limit": limit})
            assert response.status_code == 200

    @pytest.mark.parametrize("limit", [0, 101])
    async def test_limit_out_of_range_returns_422(
        self, client: AsyncClient, limit: int
    ) -> None:
        response = await client.get("/api/v1/products", params={"limit": limit})
        assert response.status_code == 422

    async def test_offset_beyond_total_returns_empty_page(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        await make_product(session)
        await session.commit()

        response = await client.get("/api/v1/products", params={"offset": 50})

        assert response.status_code == 200
        assert response.json()["items"] == []
        assert response.json()["total"] == 1


class TestProductDetail:
    async def test_get_missing_product_returns_404(self, client: AsyncClient) -> None:
        response = await client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_existing_product_returns_full_card(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await session.commit()

        response = await client.get(f"/api/v1/products/{product.product_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["category"]["category_id"] == str(product.category_id)
        assert body["manufacturer"]["manufacturer_id"] == str(product.manufacturer_id)
        assert body["average_rating"] is None


class TestReviewProductIdMismatch:
    async def test_path_and_body_product_id_mismatch_returns_422(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await session.commit()
        other_id = uuid.uuid4()

        response = await client.post(
            f"/api/v1/products/{product.product_id}/reviews",
            json={
                "product_id": str(other_id),
                "user_name": "Alice",
                "user_email": "alice@example.com",
                "rating": 5,
            },
        )

        assert response.status_code == 422