FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md main.py ./
COPY src ./src
COPY .env.example ./.env.example

RUN uv sync --frozen --no-dev

RUN mkdir -p /app/data

CMD ["uv", "run", "python", "main.py"]
