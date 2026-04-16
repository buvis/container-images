FROM python:3.14-alpine@sha256:27ac3ba1699f7a526ad19bf0d35c12369b43d3439e08297a880398d97899c3d8

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
RUN pip install --no-cache-dir --user \
    GitPython==3.1.44 \
    LinkChecker==10.5.0 \
    PyYAML==6.0.2 \
    requests==2.32.3

# Add application code
ADD --chown=app:app container-files/syncer /app

EXPOSE 9000

CMD ["python3", "/app/run.py"]
