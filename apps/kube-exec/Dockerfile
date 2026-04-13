FROM python:3@sha256:3de5d55a43a58c09ed47952b15d87ea8d18d82bc616a9277b9ddd0e6dd25b3f0

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
