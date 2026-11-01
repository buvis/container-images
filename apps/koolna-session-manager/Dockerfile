FROM debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4
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
