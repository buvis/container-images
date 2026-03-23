FROM python:3@sha256:987682ccc342b784858af8037d6ccd9ee7c37ba3b3a5f3bd69c8faa2459a651a

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
