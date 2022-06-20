ARG VERSION

FROM debian:${VERSION}

ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM:-linux/amd64}

# DEBIAN_FRONTEND: https://askubuntu.com/questions/972516/debian-frontend-environment-variable
# APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE: http://stackoverflow.com/questions/48162574/ddg#49462622
ENV \
  VERSION="${VERSION}" \
  DEBCONF_NONINTERACTIVE_SEEN=true \
  DEBIAN_FRONTEND="noninteractive" \
  APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn \
  UMASK=0002

RUN \
  adduser kah \
  --uid 568 \
  --group \
  --system \
  --disabled-password \
  --no-create-home \
  && \
  mkdir -p /config \
  && chown -R kah:kah /config \
  && chmod -R 775 /config

WORKDIR /app

# hadolint ignore=DL3008,DL3015
RUN \
  set -eux \
  && echo 'APT::Install-Recommends "false";' >/etc/apt/apt.conf.d/00recommends \
  && echo 'APT::Install-Suggests "false";' >>/etc/apt/apt.conf.d/00recommends \
  && echo 'APT::Get::Install-Recommends "false";' >>/etc/apt/apt.conf.d/00recommends \
  && echo 'APT::Get::Install-Suggests "false";' >>/etc/apt/apt.conf.d/00recommends \
  && \
  apt-get -qq update \
  && \
  apt-get install -y \
    bash \
    ca-certificates \
    curl \
    dnsutils \
    jq \
    locales \
    lsb-release \
    tini \
    tzdata \
    vim-tiny \
  && \
  localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
  && ln -s /usr/bin/vim.tiny /usr/local/bin/vi \
  && ln -s /usr/bin/vim.tiny /usr/local/bin/vim \
  && ln -s /usr/bin/vim.tiny /usr/local/bin/nano \
  && ln -s /usr/bin/vim.tiny /usr/local/bin/emacs \
  && chown -R kah:kah /app \
  && \
  printf "/bin/bash /shim/greeting.sh\n" >> /etc/bash.bashrc \
  && \
  && dpkgArch=$(dpkg --print-architecture) \
  && if [ "$dpkgArch" = "armhf" ]; then \
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 04EE7237B7D453EC 648ACFD622F3D138 \
        && echo "deb http://deb.debian.org/debian buster-backports main" | tee -a /etc/apt/sources.list.d/buster-backports.list \
        && apt update \
        && apt install -t buster-backports libseccomp2 ;\
  && fi \
  && apt-get remove -y jq \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get autoremove -y \
  && apt-get clean \
  && \
  rm -rf \
    /tmp/* \
    /var/lib/apt/lists/* \
    /var/cache/apt/* \
    /var/tmp/*

ENV LANG en_US.UTF-8

USER kah

VOLUME [ "/config" ]

COPY ./base/debian-slim/shim /shim

ENTRYPOINT [ "/usr/bin/tini", "--" ]

LABEL \
  org.opencontainers.image.base.name="ghcr.io/buvis/debian-slim:${VERSION}" \
  org.opencontainers.image.authors="Tomas Bouska <tomas@buvis.net>"
