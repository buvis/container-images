FROM python:3@sha256:b370b01487e7e82d0ef36bad3da30fc66f3466444b9157f28bb4fec6b5023d4b

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
