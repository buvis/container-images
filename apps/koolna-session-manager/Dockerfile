FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
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
