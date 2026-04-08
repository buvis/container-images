FROM python:3@sha256:9234c2fd80143741d28153f66dc306f0448c477a7d965df83107373411509357

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
