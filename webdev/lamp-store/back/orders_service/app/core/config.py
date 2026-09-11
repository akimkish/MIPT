from functools import lru_cache

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки orders_service, читаемые из окружения.

    Attributes:
        database_url: Строка подключения к БД orders_service (async, asyncpg).
        jwt_public_key_b64: Публичный ключ RS256 в base64 для проверки подписи
            JWT (используется только на admin-эндпоинте смены статуса заказа).
        jwt_algorithm: Алгоритм подписи JWT, ожидаемый в токене.
        jwt_issuer: Ожидаемое значение claim "iss".
        jwt_audience: Ожидаемое значение claim "aud".
        jwt_leeway_seconds: Допуск на расхождение часов при проверке "exp".
        internal_api_key: Секрет для заголовка X-Internal-Token при исходящих
            запросах к products_service (orders_service здесь клиент).
        products_service_url: Базовый URL products_service.
        products_service_timeout_connect: Таймаут установления соединения
            с products_service, секунды.
        products_service_timeout_read: Таймаут чтения ответа от
            products_service, секунды (reserve — самая тяжёлая операция).
        app_port: Порт, на котором приложение слушает внутри контейнера.
        log_level: Уровень логирования.
        db_connect_attempts: Число попыток подключения к БД при старте.
        db_connect_delay: Пауза между попытками подключения к БД, секунды.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Обязательные — без дефолта, отсутствие переменной должно валить старт.
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    jwt_public_key_b64: str = Field(alias="JWT_PUBLIC_KEY_B64")
    internal_api_key: str = Field(alias="INTERNAL_API_KEY")
    products_service_url: AnyHttpUrl = Field(alias="PRODUCTS_SERVICE_URL")

    # Необязательные — с дефолтами.
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="admin_service", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="lamp-store", alias="JWT_AUDIENCE")
    jwt_leeway_seconds: int = Field(default=10, alias="JWT_LEEWAY_SECONDS")

    app_port: int = Field(default=8002, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    db_connect_attempts: int = Field(default=10, alias="DB_CONNECT_ATTEMPTS")
    db_connect_delay: float = Field(default=1.0, alias="DB_CONNECT_DELAY")

    # Таймауты HTTP-клиента к products_service. Полей retry/backoff здесь
    # нет намеренно: ретраев в проекте нет нигде (см. INTEGRATION_CONTRACT.md,
    # rejected_alternatives) — одна попытка, а тип исключения решает исход.
    products_service_timeout_connect: float = Field(
        default=3.0, alias="PRODUCTS_SERVICE_TIMEOUT_CONNECT"
    )
    products_service_timeout_read: float = Field(
        default=10.0, alias="PRODUCTS_SERVICE_TIMEOUT_READ"
    )


@lru_cache
def get_settings() -> Settings:

    return Settings()
