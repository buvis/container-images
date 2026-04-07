FROM python:3@sha256:0b45a7265e3d6f3cbe81b09907772245c4c319b8bc8fb9f5a4088cd2b7ba66c6

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
