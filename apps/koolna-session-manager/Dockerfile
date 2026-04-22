FROM debian:trixie-slim@sha256:e02d6676e4dc2633fe045d6435d6039396736055976136f71ee5b77498f96fcf
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
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
