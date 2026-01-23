FROM python:3.12-slim

RUN groupadd -g 1001 buvis && useradd -u 1001 -g buvis -m -d /app buvis

WORKDIR /app

# Install uv via pip (version pinned, verified via PyPI checksums)
RUN pip install --no-cache-dir uv==0.5.14

COPY --chown=buvis:buvis pyproject.toml uv.lock ./
COPY --chown=buvis:buvis app/ app/

USER buvis
RUN uv sync --frozen

EXPOSE 8000
VOLUME /data
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["/app/.venv/bin/uvicorn", "app.main:get_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
