"""Конфигурация сервиса products_service.

Все настройки читаются один раз из переменных окружения / .env через
pydantic-settings и переиспользуются как синглтон (см. get_settings).
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки products_service, читаемые из окружения.

    Attributes:
        database_url: Строка подключения к БД products_service (async, asyncpg).
        jwt_public_key_b64: Публичный ключ RS256 в base64 для проверки подписи JWT.
        jwt_algorithm: Алгоритм подписи JWT, ожидаемый в токене.
        jwt_issuer: Ожидаемое значение claim "iss".
        jwt_audience: Ожидаемое значение claim "aud".
        jwt_leeway_seconds: Допуск на расхождение часов при проверке "exp".
        internal_api_key: Секрет для аутентификации internal-эндпоинтов
            (заголовок X-Internal-Token), общий с orders_service.
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
    database_url: str = Field(alias="DATABASE_URL")
    jwt_public_key_b64: str = Field(alias="JWT_PUBLIC_KEY_B64")
    internal_api_key: str = Field(alias="INTERNAL_API_KEY")

    # Необязательные — с дефолтами.
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="admin_service", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="lamp-store", alias="JWT_AUDIENCE")
    jwt_leeway_seconds: int = Field(default=10, alias="JWT_LEEWAY_SECONDS")

    app_port: int = Field(default=8001, alias="APP_PORT")

    sql_echo: bool = False
    db_connect_attempts: int = Field(default=10, alias="DB_CONNECT_ATTEMPTS")
    db_connect_delay: float = Field(default=1.0, alias="DB_CONNECT_DELAY")


@lru_cache
def get_settings() -> Settings:
    """Возвращает закешированный singleton-экземпляр Settings.

    lru_cache без параметров кеширует по единственному вызову без аргументов,
    поэтому .env читается и парсится один раз за жизнь процесса, а не на
    каждый Depends(get_settings) в FastAPI.

    Returns:
        Единственный экземпляр Settings на процесс.
    """
    return Settings()
