FROM python:3@sha256:0040600478fe761fbaea26b16cb4ce1b520e5aa1cef26d0762c538ece5892c02

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
