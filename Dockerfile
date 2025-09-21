FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:$PATH"

RUN apt update
RUN apt install unzip wget curl sudo -y
RUN curl -LsSf https://astral.sh/uv/install.sh | sh


WORKDIR /app

COPY . .

WORKDIR /app/src
CMD ["uv", "sync"]
CMD ["uv", "run", "main.py"]