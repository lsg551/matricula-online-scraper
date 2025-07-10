FROM python:3.13-alpine as builder

WORKDIR /app

ENV UV_LINK_MODE=copy
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,relabel=shared \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,relabel=shared \
    uv sync --locked --no-install-project --no-dev
# uv sync --locked --compile-bytecode --no-install-project --no-dev

ADD . /app

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Clean up unnecessary files from venv
RUN find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + && \
    find /app/.venv -name "*.pyo" -delete && \
    find /app/.venv -name "*.so" -exec strip {} \; && \
    find /app/.venv -type f -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true \
    rm -rf /app/.venv/lib/python*/site-packages/*/tests && \
    rm -rf /app/.venv/lib/python*/site-packages/*/*test* && \
    find /app/.venv -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true


# --- runtime stage ---
FROM python:3.13-alpine AS runtime
LABEL org.opencontainers.image.title="matricula-online-scraper"
LABEL org.opencontainers.image.description="Scraper for Matricula Online."
LABEL org.opencontainers.image.url="https://github.com/lsg551/matricula-online-scraper"
LABEL org.opencontainers.image.source="https://github.com/lsg551/matricula-online-scraper"
LABEL org.opencontainers.image.documentation="https://github.com/lsg551/matricula-online-scraper#readme"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Luis Schulte <git@luisschulte.com>"
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Copy only the virtual environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/matricula_online_scraper /app/matricula_online_scraper
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

ENTRYPOINT [ "matricula-online-scraper" ]
CMD ["--help"]
