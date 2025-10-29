FROM ghcr.io/astral-sh/uv:python-3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt update && apt upgrade -y && apt install -y unzip wget curl sudo git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN uv sync

WORKDIR /app/src

CMD ["uv", "run", "main.py"]