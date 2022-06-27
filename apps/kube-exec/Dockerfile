FROM python:3

WORKDIR /app

COPY ./apps/kube-exec/scripts/kube_exec.py ./
COPY ./apps/kube-exec/requirements.txt ./
COPY ./apps/kube-exec/entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
