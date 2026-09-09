# admin_service/app/core/config.py
"""Конфигурация сервиса admin_service.

Все настройки читаются один раз из переменных окружения / .env через
pydantic-settings и переиспользуются как синглтон (см. get_settings).
"""

from functools import lru_cache

from pydantic import EmailStr, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
import base64

class Settings(BaseSettings):
    """Настройки admin_service, читаемые из окружения.

    Attributes:
        database_url: Строка подключения к БД admin_service (async, asyncpg).
        jwt_private_key_b64: Приватный ключ RS256 в base64 для подписи
            выпускаемых JWT. Есть только в admin_service.
        jwt_public_key_b64: Публичный ключ RS256 в base64 для проверки
            подписи JWT на собственных защищённых эндпоинтах.
        jwt_algorithm: Алгоритм подписи JWT.
        jwt_issuer: Значение claim "iss", кладётся в выпускаемые токены.
        jwt_audience: Значение claim "aud", кладётся в выпускаемые токены.
        jwt_leeway_seconds: Допуск на расхождение часов при проверке "exp".
        access_token_ttl_minutes: Срок жизни access-токена, минуты.
        first_admin_email: Email первого суперадмина для бутстрапа при
            пустой таблице admins.
        first_admin_password: Пароль первого суперадмина (в открытом виде,
            только для однократного хеширования при бутстрапе).
        max_failed_login_attempts: Порог неудачных входов до блокировки.
        lockout_duration_minutes: Длительность блокировки после превышения
            порога, минуты.
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
    jwt_private_key_b64: str = Field(alias="JWT_PRIVATE_KEY_B64")
    jwt_public_key_b64: str = Field(alias="JWT_PUBLIC_KEY_B64")
    first_admin_email: str = Field(alias="FIRST_ADMIN_EMAIL")
    first_admin_password: str = Field(alias="FIRST_ADMIN_PASSWORD")

    # Необязательные — с дефолтами.
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="admin_service", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="lamp-store", alias="JWT_AUDIENCE")
    jwt_leeway_seconds: int = Field(default=10, alias="JWT_LEEWAY_SECONDS")
    access_token_ttl_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_TTL_MINUTES"
    )

    max_failed_login_attempts: int = Field(
        default=5, alias="MAX_FAILED_LOGIN_ATTEMPTS"
    )
    lockout_duration_minutes: int = Field(
        default=15, alias="LOCKOUT_DURATION_MINUTES"
    )

    app_port: int = Field(default=8003, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    db_connect_attempts: int = Field(default=10, alias="DB_CONNECT_ATTEMPTS")
    db_connect_delay: float = Field(default=1.0, alias="DB_CONNECT_DELAY")


    @property
    def jwt_private_key(self) -> str:
        """Приватный ключ RS256 в виде PEM-текста (декодирован из base64).

        Returns:
            PEM-представление приватного ключа с переносами строк.
        """
        return base64.b64decode(self.jwt_private_key_b64).decode("utf-8")

    @property
    def jwt_public_key(self) -> str:
        """Публичный ключ RS256 в виде PEM-текста (декодирован из base64).

        Returns:
            PEM-представление публичного ключа с переносами строк.
        """
        return base64.b64decode(self.jwt_public_key_b64).decode("utf-8")
@lru_cache
def get_settings() -> Settings:
    """Возвращает закешированный singleton-экземпляр Settings.

    Returns:
        Единственный экземпляр Settings на процесс.
    """
    return Settings()