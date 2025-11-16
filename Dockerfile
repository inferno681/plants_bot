FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* /app/

RUN uv sync --no-dev --frozen --no-cache

RUN uv pip install --no-deps --system .

RUN mkdir -p ./src

COPY ./src/config  ./src/config

COPY ./src/bot  ./src/bot

ENV PYTHONPATH=/app/src/
RUN python -m site

CMD ["python", "src/bot/main.py"]
