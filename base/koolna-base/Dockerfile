FROM golang:1.22-alpine AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ ./cmd/
RUN CGO_ENABLED=0 go build -o koolna ./cmd/koolna

FROM debian:trixie-slim

ARG GOTTY_VERSION=1.6.0
ARG USERNAME=bob
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  git \
  tmux \
  ca-certificates \
  gnupg \
  lsb-release \
  sudo \
  vim \
  less \
  lazygit \
  vifm \
  nodejs \
  && rm -rf /var/lib/apt/lists/*

RUN arch="$(dpkg --print-architecture)" \
  && curl -fsSL -o /tmp/gotty.tar.gz "https://github.com/sorenisanerd/gotty/releases/download/v${GOTTY_VERSION}/gotty_v${GOTTY_VERSION}_linux_${arch}.tar.gz" \
  && tar -xzf /tmp/gotty.tar.gz -C /tmp \
  && install -m 0755 /tmp/gotty /usr/local/bin/gotty \
  && rm -f /tmp/gotty.tar.gz /tmp/gotty

RUN if [ ! -e /usr/bin/node ] && [ -e /usr/bin/nodejs ]; then ln -s /usr/bin/nodejs /usr/bin/node; fi

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && usermod -aG sudo $USERNAME \
  && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME

RUN mkdir -p /workspace /home/$USERNAME/.local/bin \
  && chown -R $USERNAME:$USERNAME /home/$USERNAME \
  && chown $USERNAME:$USERNAME /workspace

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

COPY --chown=${USERNAME}:${USERNAME} assets/config/tmux.conf /home/$USERNAME/.tmux.conf
COPY --from=builder /build/koolna /usr/local/bin/koolna

COPY assets/bin/startup.sh /usr/local/bin/startup.sh
COPY assets/bin/respawn-shell.sh /usr/local/bin/respawn-shell.sh
COPY assets/bin/start-gotty.sh /usr/local/bin/start-gotty.sh
COPY assets/bin/tmux-clipboard-server.js /usr/local/bin/tmux-clipboard-server.js
COPY assets/bin/tmux-clipboard-copy.sh /usr/local/bin/tmux-clipboard-copy.sh

COPY assets/web/ /usr/share/koolna/web/

RUN chmod +x /usr/local/bin/koolna \
  && chmod +x /usr/local/bin/startup.sh \
  && chmod +x /usr/local/bin/respawn-shell.sh \
  && chmod +x /usr/local/bin/start-gotty.sh \
  && chmod +x /usr/local/bin/tmux-clipboard-server.js \
  && chmod +x /usr/local/bin/tmux-clipboard-copy.sh

WORKDIR /workspace

RUN chown -R $USERNAME:$USERNAME /usr/share/koolna

EXPOSE 3000

USER $USERNAME

CMD ["/usr/local/bin/startup.sh"]
