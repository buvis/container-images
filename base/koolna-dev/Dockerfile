FROM ghcr.io/buvis/koolna-base:latest@sha256:b4612ce17970262944a8514013c4961d28b0f23bc99a44b775f73dbf850c0733

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

# Runtime convenience: kept for users adding cargo: tools at runtime.
# The installer is vendored (reviewed in git) instead of curl'd at build time. Pairing a
# Renovate-tracked ARG *_VERSION with a static ARG *_SHA256 is unbumpable: Renovate raises
# the version but cannot know the new script's hash, so every bump fails `sha256sum -c`.
# The script honours BINSTALL_VERSION to pick the release, so version tracking survives.
# renovate: datasource=github-releases depName=cargo-bins/cargo-binstall
ARG CARGO_BINSTALL_VERSION=v1.19.0
COPY --chown=${USERNAME}:${USERNAME} assets/install-binstall.sh /tmp/install-binstall.sh
RUN BINSTALL_VERSION="${CARGO_BINSTALL_VERSION}" bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

CMD ["sh", "-c", "exec sleep infinity"]
