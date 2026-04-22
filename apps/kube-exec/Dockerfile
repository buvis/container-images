FROM python:3@sha256:ef1efc7276a14c09645bf6fdb0a9f11065dab3d30c80d9a1a7dc7f1e66be8398

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
