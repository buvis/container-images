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

# Use the existing `node` user (uid 1000) shipped with node:24-trixie-slim
USER node
WORKDIR /home/node

COPY --chown=node:node broker.py /app/broker.py

ENV HOME=/home/node
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/app/broker.py"]
