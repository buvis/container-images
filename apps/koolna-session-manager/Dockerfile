FROM debian:trixie-slim@sha256:020c0d20b9880058cbe785a9db107156c3c75c2ac944a6aa7ab59f2add76a7bd
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
