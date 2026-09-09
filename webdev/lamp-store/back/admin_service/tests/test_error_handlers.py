"""Единый конверт ошибок и обработчики исключений. Раздел 7."""

import json

import pytest
from starlette.requests import Request

from app.core.exceptions import EXCEPTION_MAPPING, resolve_error_mapping
from app.main import service_error_handler, unhandled_exception_handler
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


def _fake_request() -> Request:
    """Минимальный объект Request для обработчиков, которые его не читают."""
    return Request(scope={"type": "http", "method": "GET", "path": "/", "headers": []})


class TestErrorMapping:
    @pytest.mark.parametrize("exc_type", list(EXCEPTION_MAPPING.keys()))
    def test_every_registered_exception_resolves_to_itself_or_parent(
        self, exc_type
    ) -> None:
        """Каждый зарегистрированный тип разрешается в своё собственное правило."""
        # ServiceError напрямую не инстанцируется в реальном коде, но
        # достаточно проверить резолюцию для конкретных подклассов.
        if exc_type is ServiceError:
            instance = ServiceError("base")
        else:
            instance = exc_type("test message")

        mapping = resolve_error_mapping(instance)
        assert mapping.status_code == EXCEPTION_MAPPING[exc_type].status_code
        assert mapping.code == EXCEPTION_MAPPING[exc_type].code

    def test_unregistered_subclass_falls_back_to_nearest_parent(self) -> None:
        """Незарегистрированный подкласс NotFoundError наследует его правило."""

        class VerySpecificNotFound(NotFoundError):
            pass

        mapping = resolve_error_mapping(VerySpecificNotFound("specific"))
        assert mapping == EXCEPTION_MAPPING[NotFoundError]


@pytest.mark.asyncio
class TestExceptionHandlers:
    async def test_service_error_handler_returns_mapped_status_and_code(self) -> None:
        """service_error_handler отдаёт статус/код по EXCEPTION_MAPPING."""
        response = await service_error_handler(_fake_request(), ConflictError("dup"))

        assert response.status_code == 409
        body = json.loads(response.body)
        assert body["code"] == "CONFLICT"
        assert body["message"] == "dup"

    async def test_unhandled_exception_handler_hides_internal_details(self) -> None:
        """unhandled_exception_handler не отдаёт текст исходного исключения наружу."""
        response = await unhandled_exception_handler(
            _fake_request(), RuntimeError("leaked secret detail")
        )

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["code"] == "INTERNAL_ERROR"
        assert "leaked secret detail" not in body["message"]


@pytest.mark.asyncio
async def test_validation_error_uses_unified_envelope(client) -> None:
    """422 от Pydantic приходит в едином конверте, не в дефолтном {"detail": [...]}."""
    response = await client.post(
        "/api/v1/auth/login", json={"email": "not-an-email", "password": ""}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "detail" not in body
    assert isinstance(body["details"], list)