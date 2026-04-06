FROM ghcr.io/buvis/koolna-base:latest@sha256:a67dae2115c823d9b4dec236e3245a54cd1d8e6b6ca9c7eef8bf493bb9a9bbe5

ARG USERNAME=bob

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

USER $USERNAME

ENV HOME=/home/$USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

RUN curl -L --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash

RUN $HOME/.cargo/bin/cargo-binstall -y zoxide rumdl

CMD ["sh", "-c", "exec sleep infinity"]
