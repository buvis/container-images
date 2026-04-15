FROM python:3@sha256:63fdc2bca05b142ef64d05e8f9dbc4e8bf9f51294824db5c3d8b10f419fe1bdd

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
