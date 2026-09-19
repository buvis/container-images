FROM python:3@sha256:a2e9788143507cacbb754fcc06ad3b7108ca9c334f97a466906103846107cdd5

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
