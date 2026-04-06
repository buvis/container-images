FROM python:3.13-slim-trixie

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
