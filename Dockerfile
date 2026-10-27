FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt update && apt upgrade -y && apt install -y unzip wget curl sudo git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

RUN uv sync

COPY . .

WORKDIR /app/src

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "API:app"]
