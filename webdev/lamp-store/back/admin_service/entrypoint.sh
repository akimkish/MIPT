#!/bin/sh


APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8003}"

echo "[entrypoint] Ожидание готовности БД..."
python -m app.db.database

echo "[entrypoint] Применение миграций Alembic..."
alembic upgrade head

echo "[entrypoint] Запуск uvicorn на ${APP_HOST}:${APP_PORT}..."
exec uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}"