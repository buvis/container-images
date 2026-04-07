FROM ghcr.io/buvis/koolna-base:latest@sha256:a67dae2115c823d9b4dec236e3245a54cd1d8e6b6ca9c7eef8bf493bb9a9bbe5

ARG USERNAME=bob

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.cargo/bin:$PATH"

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

ARG CARGO_BINSTALL_VERSION=v1.17.9
ARG CARGO_BINSTALL_SHA256=c2e963fbab3bdd8653b59c28d349bf85740cf4998e5e398d250dcd2884cd667d
RUN curl -fsSL "https://raw.githubusercontent.com/cargo-bins/cargo-binstall/${CARGO_BINSTALL_VERSION}/install-from-binstall-release.sh" -o /tmp/install-binstall.sh \
  && echo "${CARGO_BINSTALL_SHA256}  /tmp/install-binstall.sh" | sha256sum -c - \
  && bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

RUN $HOME/.cargo/bin/cargo-binstall -y zoxide rumdl

CMD ["sh", "-c", "exec sleep infinity"]
