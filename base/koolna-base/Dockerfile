FROM debian:trixie-slim@sha256:26f98ccd92fd0a44d6928ce8ff8f4921b4d2f535bfa07555ee5d18f61429cf0c

ARG USERNAME=bob
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  tmux \
  ca-certificates \
  gnupg \
  dirmngr \
  lsb-release \
  sudo \
  vim \
  less \
  lazygit \
  vifm \
  python3 \
  python3-pip \
  python3-venv \
  zsh \
  fish \
  && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/$(dpkg --print-architecture)/kubectl" -o /tmp/kubectl \
  && install -m 0755 /tmp/kubectl /usr/local/bin/kubectl \
  && rm /tmp/kubectl

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && usermod -aG sudo $USERNAME \
  && echo "$USERNAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt, /usr/bin/dpkg, /usr/bin/snap, /usr/local/bin/mise, /bin/systemctl, /usr/sbin/service" > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME

RUN mkdir -p /workspace /home/$USERNAME/.local/bin /home/$USERNAME/.config/mise \
  && chown -R $USERNAME:$USERNAME /home/$USERNAME \
  && chown $USERNAME:$USERNAME /workspace

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:/usr/local/bin:$PATH"
ENV MISE_DATA_DIR="$HOME/.local/share/mise"
ENV MISE_CONFIG_DIR="$HOME/.config/mise"
ENV MISE_CACHE_DIR="$HOME/.cache/mise"
ENV MISE_NODE_DEFAULT_PACKAGES_FILE="$HOME/.default-npm-packages"
ENV MISE_TRUSTED_CONFIG_PATHS="/workspace"
ENV MISE_IDIOMATIC_VERSION_FILE_ENABLE_TOOLS="false"

COPY --chown=${USERNAME}:${USERNAME} assets/config/.default-npm-packages /home/$USERNAME/.default-npm-packages
COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml
COPY --chown=${USERNAME}:${USERNAME} assets/config/tmux.conf /home/$USERNAME/.tmux.conf

RUN echo 'eval "$(mise activate bash)"' >> ~/.bashrc \
  && echo 'export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"' >> ~/.profile \
  && MISE_VERSION="2025.5.6" \
  && curl -fsSL "https://mise.jdx.dev/v${MISE_VERSION}/install.sh" -o /tmp/mise-install.sh \
  && sh /tmp/mise-install.sh \
  && rm /tmp/mise-install.sh

# Import Node.js release signing keys for GPG verification
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  && gpg --batch --export 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 | gpg --import

RUN bash -c 'eval "$(mise activate bash)" && mise install'

USER root

RUN cp /home/$USERNAME/.local/bin/mise /usr/local/bin/mise

COPY assets/lib/whatwedo /usr/local/lib/whatwedo
COPY assets/bin/whatwedo /usr/local/bin/whatwedo

RUN chmod +x /usr/local/lib/whatwedo \
  && chmod +x /usr/local/bin/whatwedo

WORKDIR /workspace

USER $USERNAME

CMD ["sh", "-c", "exec sleep infinity"]
