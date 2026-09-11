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
