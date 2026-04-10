FROM python:3@sha256:8428c32065df71d5a7763099ccb8ee215314129b50d395f95ad589151887d52f

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
