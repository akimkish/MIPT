from __future__ import annotations

import logging
from typing import Any

import httpx

from app.clients.exceptions import (
    ServiceRejectedError,
    ServiceUnavailableError,
    ServiceUnknownStateError,
)
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)


class BaseServiceClient:
    def __init__(
        self,
        *,
        base_url: str,
        service_name: str,
        connect_timeout: float,
        read_timeout: float,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Создаёт клиент с фиксированными таймаутами.

        Args:
            base_url: Базовый URL сервиса, например http://products_service:8000.
            service_name: Имя сервиса для логов и сообщений об ошибках.
            connect_timeout: Таймаут установки соединения, секунды.
            read_timeout: Таймаут ожидания ответа, секунды.
            headers: Заголовки, добавляемые к каждому запросу (например,
                X-Internal-Token).
        """
        self._service_name = service_name
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=read_timeout,
                pool=connect_timeout,
            ),
            headers=headers or {},
        )

    async def aclose(self) -> None:
        """Закрывает пул соединений. Вызывается на shutdown приложения."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: Any | None = None,
    ) -> httpx.Response:
        """Выполняет ОДИН HTTP-запрос и разбирает результат.

        Args:
            method: HTTP-метод, например "POST".
            url: Путь относительно base_url, например "/api/v1/internal/stock/reserve".
            json: Тело запроса (уже сериализуемое в JSON).

        Returns:
            Ответ со статусом 2xx.

        """
        request_id = get_request_id()
        headers = {"X-Request-ID": request_id} if request_id else {}

        try:
            response = await self._client.request(
                method, url, json=json, headers=headers
            )
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error(
                "%s %s %s failed: connection not established (%s) request_id=%s",
                self._service_name,
                method,
                url,
                type(exc).__name__,
                request_id,
            )
            raise ServiceUnavailableError(
                f"{self._service_name} is unreachable",
                reason=type(exc).__name__,
            ) from exc
        except httpx.TimeoutException as exc:
            # ReadTimeout/WriteTimeout/PoolTimeout: запрос уже отправлен.
            logger.error(
                "%s %s %s timed out after send (%s) request_id=%s",
                self._service_name,
                method,
                url,
                type(exc).__name__,
                request_id,
            )
            raise ServiceUnknownStateError(
                f"{self._service_name} did not answer in time",
                reason=type(exc).__name__,
            ) from exc
        except httpx.HTTPError as exc:
            # Например RemoteProtocolError: соединение оборвалось на полпути.
            logger.error(
                "%s %s %s transport error (%s) request_id=%s",
                self._service_name,
                method,
                url,
                type(exc).__name__,
                request_id,
            )
            raise ServiceUnknownStateError(
                f"{self._service_name} transport error",
                reason=type(exc).__name__,
            ) from exc

        if response.status_code >= 500:
            logger.error(
                "%s %s %s returned %s request_id=%s body=%s",
                self._service_name,
                method,
                url,
                response.status_code,
                request_id,
                response.text[:500],
            )
            raise ServiceUnknownStateError(
                f"{self._service_name} returned {response.status_code}",
                reason=f"http_{response.status_code}",
            )

        if response.status_code >= 400:
            body = self.error_body(response)
            code = body.get("code")
            code = str(code) if code is not None else None
            logger.warning(
                "%s %s %s returned %s code=%s request_id=%s",
                self._service_name,
                method,
                url,
                response.status_code,
                code,
                request_id,
            )
            raise ServiceRejectedError(
                f"{self._service_name} rejected request with "
                f"{response.status_code}",
                reason=f"http_{response.status_code}",
                status_code=response.status_code,
                code=code,
                body=body,
            )

        return response

    @staticmethod
    def error_body(response: httpx.Response) -> dict[str, Any]:
        """Разбирает тело ответа в общий конверт ошибки.

        Args:
            response: Ответ сервиса со статусом 4xx.

        Returns:
            Словарь с ключами code/message/details. Если тело не JSON,
            возвращается пустой словарь — падать на разборе ошибки нельзя.
        """
        try:
            body = response.json()
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}
