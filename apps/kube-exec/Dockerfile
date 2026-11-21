FROM python:3@sha256:46837ed3105db0029b6d656816185c6258e3b39690532fb782428e0a5fd76182

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
