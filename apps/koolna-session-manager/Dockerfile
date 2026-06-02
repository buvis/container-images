FROM debian:trixie-slim@sha256:b6e2a152f22a40ff69d92cb397223c906017e1391a73c952b588e51af8883bf8
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
  tmux \
  util-linux \
  git \
  curl \
  ca-certificates \
  openssh-server \
  && rm -rf /var/lib/apt/lists/*
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TERM=xterm-256color
COPY entrypoint.sh /entrypoint.sh
COPY lib.sh /lib.sh
COPY koolna-attach.sh /usr/local/bin/koolna-attach
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
