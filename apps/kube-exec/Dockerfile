FROM python:3

WORKDIR /usr/src/app

ADD ./apps/kube-exec/scripts/cleanupZk.py ./

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/entrypoint.sh"]
