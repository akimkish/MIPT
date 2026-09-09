from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    db_port: str

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
