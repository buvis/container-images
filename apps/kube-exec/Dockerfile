FROM python:3@sha256:61346539f7b26521a230e72c11da5ebd872924745074b19736e7d65ba748c366

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
