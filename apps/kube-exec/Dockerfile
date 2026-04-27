FROM python:3@sha256:0ba001803c72c128063cfa88863755f905cefabe73c026c66a5a86d8f1d63e98

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
