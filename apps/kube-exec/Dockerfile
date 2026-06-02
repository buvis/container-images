FROM python:3@sha256:250e5c97be05e1eb2272fbdbd810dfd638f9012e1e6f65c99390ad3239943a08

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
