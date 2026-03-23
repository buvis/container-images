FROM python:3@sha256:ffebef43892dd36262fa2b042eddd3320d5510a21f8440dce0a650a3c124b51d

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
