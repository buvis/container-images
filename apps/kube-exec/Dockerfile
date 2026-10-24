FROM python:3@sha256:67ee282bdbe5ece1e38ea94fa68f1420e969e6176e6c826b9acc931055011bfb

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
