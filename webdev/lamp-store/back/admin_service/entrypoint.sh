#!/bin/sh

#
# Порядок шагов принципиален и зафиксирован в PROMPT_CONTEXT.md
# (domain_decisions → «Старт сервиса и готовность БД»):
#   1. Дождаться готовности БД (wait_for_db.py) — без этого шага alembic
#      упадёт первым при недоступной БД с менее понятной ошибкой.
#   2. Применить миграции (alembic upgrade head) — до старта uvicorn,
#      иначе первый же запрос к API получит relation does not exist.
#   3. Запустить uvicorn — только после шагов 1–2, поэтому сам факт
#      того, что сервис начал принимать HTTP-запросы, уже означает,
#      что GET /health может отвечать 200 без обращения к БД.
#
# set -e: любой шаг, завершившийся с ненулевым кодом, немедленно
# останавливает скрипт — так контейнер падает явно (Docker покажет
# Exited (1)), а не продолжает попытку стартовать uvicorn поверх
# несуществующей схемы БД.
set -e

# Явные значения по умолчанию для host/port uvicorn — переопределяются
# переменными окружения при необходимости (например, в docker-compose.yml
# или при локальном запуске без Docker).
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8003}"

echo "[entrypoint] Ожидание готовности БД..."
python -m app.db.database

echo "[entrypoint] Применение миграций Alembic..."
alembic upgrade head

echo "[entrypoint] Запуск uvicorn на ${APP_HOST}:${APP_PORT}..."
exec uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}"