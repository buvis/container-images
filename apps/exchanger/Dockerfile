FROM node:24-alpine@sha256:116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5 AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

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
