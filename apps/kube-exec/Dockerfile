FROM python:3@sha256:4bdca440e7381ba0d706e3718714c1a4cde97b460d8411c1af9c704bba1fba0f

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
