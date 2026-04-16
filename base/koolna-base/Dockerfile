FROM debian:trixie-slim@sha256:4ffb3a1511099754cddc70eb1b12e50ffdb67619aa0ab6c13fcd800a78ef7c7a

ARG USERNAME=bob
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  git \
  ca-certificates \
  gnupg \
  dirmngr \
  lsb-release \
  sudo \
  less \
  lazygit \
  vifm \
  zsh \
  fish \
  unzip \
  && rm -rf /var/lib/apt/lists/*

# renovate: datasource=github-releases depName=kubernetes/kubernetes extractVersion=^v(?<version>.+)$
ARG KUBECTL_VERSION=1.35.4
# renovate: datasource=github-releases depName=jdx/mise extractVersion=^v(?<version>.+)$
ARG MISE_VERSION=2026.4.14
RUN curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/$(dpkg --print-architecture)/kubectl" -o /tmp/kubectl \
  && install -m 0755 /tmp/kubectl /usr/local/bin/kubectl \
  && rm /tmp/kubectl

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && usermod -aG sudo $USERNAME \
  && echo "$USERNAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt, /usr/bin/dpkg, /usr/bin/snap, /usr/local/bin/mise, /bin/systemctl, /usr/sbin/service" > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME

RUN mkdir -p /home/$USERNAME/.local/bin /home/$USERNAME/.config/mise \
  && chown -R $USERNAME:$USERNAME /home/$USERNAME

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:/usr/local/bin:$PATH"
ENV MISE_DATA_DIR="$HOME/.local/share/mise"
ENV MISE_CONFIG_DIR="$HOME/.config/mise"
ENV MISE_CACHE_DIR="$HOME/.cache/mise"
ENV MISE_TRUSTED_CONFIG_PATHS="$HOME/workspace"
ENV MISE_IDIOMATIC_VERSION_FILE_ENABLE_TOOLS="false"

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN echo 'eval "$(mise activate bash)"' >> ~/.bashrc \
  && echo 'export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"' >> ~/.profile \
  && curl -fsSL "https://mise.jdx.dev/v${MISE_VERSION}/install.sh" -o /tmp/mise-install.sh \
  && sh /tmp/mise-install.sh \
  && rm /tmp/mise-install.sh \
  && mise install

USER root

RUN cp /home/$USERNAME/.local/bin/mise /usr/local/bin/mise

WORKDIR $HOME

USER $USERNAME

CMD ["sh", "-c", "exec sleep infinity"]
