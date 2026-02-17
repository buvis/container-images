FROM python:3@sha256:151ab3571dad616bb031052e86411e2165295c7f67ef27206852203e854bcd12

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
