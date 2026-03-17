FROM python:3@sha256:4bc0b65c0a438abef1383fbce459ae997a9689b781eb2c2ee31faf4c94585ba1

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
