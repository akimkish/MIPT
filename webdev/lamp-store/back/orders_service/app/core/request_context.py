# orders_service/app/core/request_context.py
"""Хранение X-Request-ID текущего запроса.

Идентификатор генерируется middleware на входе и должен попасть и в логи,
и в исходящий HTTP-запрос к products_service. Передавать его аргументом через
все слои (api → service → client) шумно, поэтому используется contextvar:
он живёт в рамках одной asyncio-задачи, то есть одного HTTP-запроса.

Если в проекте уже есть свой middleware с contextvar — используйте его,
а этот модуль удалите: два источника request_id хуже одного.
"""

from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str) -> None:
    """Сохраняет идентификатор текущего запроса.

    Args:
        value: Значение заголовка X-Request-ID.
    """
    _request_id.set(value)


def get_request_id() -> str | None:
    """Возвращает идентификатор текущего запроса.

    Returns:
        Значение X-Request-ID или None, если запрос пришёл вне HTTP-контекста
        (например, из теста или скрипта).
    """
    return _request_id.get()