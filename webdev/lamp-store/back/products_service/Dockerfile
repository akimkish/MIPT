# products_service/Dockerfile

# ---- Stage 1: builder — здесь ставятся зависимости в изолированный venv ----
FROM python:3.12-slim AS builder

WORKDIR /build

# gcc/libpq-dev нужны только для сборки asyncpg, в финальный образ не попадают.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Явный venv вместо системного pip install — тот же приём изоляции, что
# давал poetry virtualenvs.in-project, но без самого poetry.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем только requirements.txt — слой с pip install пересобирается лишь
# при изменении списка зависимостей, а не при каждой правке кода приложения.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: runtime — только то, что нужно для выполнения ----
FROM python:3.12-slim AS runtime

# libpq5 — рантайм-библиотека без dev-заголовков и компилятора.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY entrypoint.sh ./

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

ENTRYPOINT ["./entrypoint.sh"]