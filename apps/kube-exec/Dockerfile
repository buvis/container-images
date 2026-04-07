FROM python:3@sha256:788c343877b467e72af452878cb6d2b0ce6a16ffed973e2dc82b57d8d765eb33

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
