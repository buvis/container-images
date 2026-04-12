FROM ghcr.io/buvis/koolna-base:latest@sha256:e1c29a1089655a18914d431bd7d6fac320e8a102aac3e5917611bde9e547dcd8

ARG USERNAME=bob

# --- Build dependencies (C toolchain, pkg-config, libffi for Python/Ruby FFI) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  pkg-config \
  libffi-dev \
  && rm -rf /var/lib/apt/lists/*

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.cargo/bin:$PATH"
# --- Node.js GPG keys ---
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  || gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4

# --- Config files ---
COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

# --- Install all runtimes via mise ---
RUN bash -c 'eval "$(mise activate bash)" && mise install'

# renovate: datasource=npm depName=tree-sitter-cli
ARG TREE_SITTER_CLI_VERSION=0.26.8
RUN bash -c 'eval "$(mise activate bash)" && npm install -g tree-sitter-cli@${TREE_SITTER_CLI_VERSION}'

# renovate: datasource=github-releases depName=cargo-bins/cargo-binstall
ARG CARGO_BINSTALL_VERSION=v1.18.0
ARG CARGO_BINSTALL_SHA256=c2e963fbab3bdd8653b59c28d349bf85740cf4998e5e398d250dcd2884cd667d
RUN curl -fsSL "https://raw.githubusercontent.com/cargo-bins/cargo-binstall/${CARGO_BINSTALL_VERSION}/install-from-binstall-release.sh" -o /tmp/install-binstall.sh \
  && echo "${CARGO_BINSTALL_SHA256}  /tmp/install-binstall.sh" | sha256sum -c - \
  && bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

# renovate: datasource=crate depName=zoxide
ARG ZOXIDE_VERSION=0.9.9
# renovate: datasource=crate depName=rumdl
ARG RUMDL_VERSION=0.1.67
RUN $HOME/.cargo/bin/cargo-binstall -y zoxide@${ZOXIDE_VERSION} rumdl@${RUMDL_VERSION}

CMD ["sh", "-c", "exec sleep infinity"]
