FROM debian:trixie-slim@sha256:26f98ccd92fd0a44d6928ce8ff8f4921b4d2f535bfa07555ee5d18f61429cf0c
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
COPY entrypoint.sh /entrypoint.sh
COPY koolna-auth-init /usr/local/bin/koolna-auth-init
RUN chmod +x /entrypoint.sh /usr/local/bin/koolna-auth-init
ENTRYPOINT ["/entrypoint.sh"]
