FROM node:24-trixie-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code@latest \
    && npm cache clean --force

RUN useradd -m -u 1000 -s /bin/bash broker
USER broker
WORKDIR /home/broker

COPY --chown=broker:broker broker.py /app/broker.py

ENV HOME=/home/broker
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/app/broker.py"]
