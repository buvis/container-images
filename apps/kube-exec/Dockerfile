FROM python:3@sha256:930919e8b3161b5d0ce028592665e23265673f2dfcfc4607fb17df751156557a

WORKDIR /app

COPY ./scripts/kube_exec.py ./
COPY ./requirements.txt ./
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
