FROM python:3@sha256:df3f05ff4d74833f52146edd195c8f7913581b57796a820fb7e373457ace9bad

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
