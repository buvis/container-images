FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PATH="/home/app/.local/bin:$PATH" \
    UPDATE_INTERVAL=900

# Create app user, install git, and set up directories in one layer
RUN apk add --no-cache git && \
    adduser -D -u 1001 -h /home/app app && \
    mkdir -p /app/site && \
    chown -R app:app /app && \
    chmod -R 755 /app

USER app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir --user GitPython==3.1.44

# Add application code
ADD --chown=app:app container-files/syncer /app

CMD ["python3", "/app/run.py"]
