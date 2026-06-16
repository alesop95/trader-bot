FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# ── Dipendenze (layer cacheable) ──────────────────────────────────────────────
# Copiati prima di src/ così questo layer viene invalidato solo se cambiano
# pyproject.toml o uv.lock, non ad ogni modifica del codice sorgente.
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ── Codice sorgente + configurazione Alembic ──────────────────────────────────
COPY src/ src/
COPY alembic.ini .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Utente non-root ───────────────────────────────────────────────────────────
RUN useradd --create-home --no-log-init --shell /bin/bash trader \
    && mkdir -p /app/logs \
    && chown trader:trader /app/logs

USER trader

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

ENTRYPOINT ["trader-bot"]
