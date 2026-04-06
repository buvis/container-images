FROM python:3.14-slim-trixie@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/sh broker
USER broker
WORKDIR /home/broker

COPY --chown=broker:broker broker.py /app/broker.py

ENV HOME=/home/broker
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/app/broker.py"]
