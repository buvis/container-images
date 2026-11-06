FROM node:26-alpine@sha256:8996bb5821d62a8fd9bb27c1cb07462f3fdce6e47d640c6a881ead0b064ce216 AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim@sha256:5b3879b6f3cb77e712644d50262d05a7c146b7312d784a18eff7ff5462e77033

RUN groupadd -g 1001 buvis && useradd -u 1001 -g buvis -m -d /app buvis

WORKDIR /app

# Install uv via pip (version pinned, verified via PyPI checksums)
RUN pip install --no-cache-dir uv==0.5.14

COPY --chown=buvis:buvis pyproject.toml uv.lock ./
COPY --chown=buvis:buvis app/ app/
COPY --chown=buvis:buvis --from=frontend-builder /app/static app/static/

USER buvis
RUN uv sync --frozen

EXPOSE 8000
VOLUME /data
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["/app/.venv/bin/uvicorn", "app.main:get_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
