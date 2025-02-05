FROM python:3.9-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

WORKDIR /app

RUN uv sync --frozen --no-cache

EXPOSE 80
EXPOSE 443

ENTRYPOINT ["/app/.venv/bin/fastapi", "run", "main.py", "--port", "5000"]