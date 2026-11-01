FROM ghcr.io/buvis/koolna-base:latest@sha256:5b41aaccf5f14c104098aa2589c1d8576d7aa40e33171dda339342e175b7cf85

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
# Tools are pinned in mise config and bumped by Renovate; stop the ones that self-update at
# runtime from replacing the pinned version. buvis-gems does it synchronously on every CLI
# start (even --help), stalling first use in a fresh pod; the Copilot CLI downloads newer
# CLI versions in the background on launch.
ENV BUVIS_AUTO_UPDATE=false \
  COPILOT_AUTO_UPDATE=false
# --- Node.js GPG keys ---
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  || gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4

# --- Config files ---
COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

# --- Install all runtimes via mise ---
# python, uv and ruff installs call the GitHub API (aqua release lookups, artifact
# attestations); unauthenticated CI runners share a 60 req/h limit and get 403s. Only this
# step gets a token, as a BuildKit secret (never written to a layer). Everything else,
# including npm/cargo/pipx tools that run third-party install scripts, installs without it.
# No secret (e.g. local builds) falls back to unauthenticated requests.
# (File mount rather than env=: CI's hadolint 2.12 cannot parse the env= option.)
RUN --mount=type=secret,id=github_token,required=false,mode=0444 \
  bash -c 'if [ -s /run/secrets/github_token ]; then GITHUB_TOKEN="$(cat /run/secrets/github_token)"; export GITHUB_TOKEN; fi; eval "$(mise activate bash)" && mise install python uv ruff'
RUN bash -c 'eval "$(mise activate bash)" && mise install'

# renovate: datasource=npm depName=tree-sitter-cli
ARG TREE_SITTER_CLI_VERSION=0.27.1
RUN bash -c 'eval "$(mise activate bash)" && npm install -g tree-sitter-cli@${TREE_SITTER_CLI_VERSION}'

# Runtime convenience: kept for users adding cargo: tools at runtime.
# The installer is vendored (reviewed in git) instead of curl'd at build time. Pairing a
# Renovate-tracked ARG *_VERSION with a static ARG *_SHA256 is unbumpable: Renovate raises
# the version but cannot know the new script's hash, so every bump fails `sha256sum -c`.
# The script honours BINSTALL_VERSION to pick the release, so version tracking survives.
# renovate: datasource=github-releases depName=cargo-bins/cargo-binstall
ARG CARGO_BINSTALL_VERSION=v1.26.2
COPY --chown=${USERNAME}:${USERNAME} assets/install-binstall.sh /tmp/install-binstall.sh
RUN BINSTALL_VERSION="${CARGO_BINSTALL_VERSION}" bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

CMD ["sh", "-c", "exec sleep infinity"]
