FROM python:3.10-slim-buster

ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG VERSION

ENV DEBCONF_NONINTERACTIVE_SEEN=true \
    DEBIAN_FRONTEND='noninteractive' \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH \
    GIT_CREDENTIALS='' \
    GIT_REPO='none' \
    GIT_BRANCH='main' \
    UPDATE_INTERVAL=900

RUN set -eux && \
    echo 'APT::Install-Recommends "false";' >/etc/apt/apt.conf.d/00recommends && \
    echo 'APT::Install-Suggests "false";' >>/etc/apt/apt.conf.d/00recommends && \
    echo 'APT::Get::Install-Recommends "false";' >>/etc/apt/apt.conf.d/00recommends && \
    echo 'APT::Get::Install-Suggests "false";' >>/etc/apt/apt.conf.d/00recommends &&\
    apt-get -qq update && \
    apt-get install -y git && \
    python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir GitPython==3.1.24 && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/* /var/cache/distfiles/* && \
    adduser --disabled-login app

USER app

ADD --chown=app:app ./apps/mkdocs-git-sync/container-files/syncer /app
# use this when invoking docker-compose locally: ADD --chown=app:app container-files/syncer /app
WORKDIR /app

RUN mkdir /app/site

CMD ["python3", "/app/run.py"]
