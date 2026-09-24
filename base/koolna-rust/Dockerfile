FROM ghcr.io/buvis/koolna-base:latest@sha256:b4612ce17970262944a8514013c4961d28b0f23bc99a44b775f73dbf850c0733

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

# The installer is vendored (reviewed in git) instead of curl'd at build time. Pairing a
# Renovate-tracked ARG *_VERSION with a static ARG *_SHA256 is unbumpable: Renovate raises
# the version but cannot know the new script's hash, so every bump fails `sha256sum -c`.
# The script honours BINSTALL_VERSION to pick the release, so version tracking survives.
# renovate: datasource=github-releases depName=cargo-bins/cargo-binstall
ARG CARGO_BINSTALL_VERSION=v1.19.0
COPY --chown=${USERNAME}:${USERNAME} assets/install-binstall.sh /tmp/install-binstall.sh
RUN BINSTALL_VERSION="${CARGO_BINSTALL_VERSION}" bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

# renovate: datasource=crate depName=zoxide
ARG ZOXIDE_VERSION=0.9.9
# renovate: datasource=crate depName=rumdl
ARG RUMDL_VERSION=0.1.67
RUN $HOME/.cargo/bin/cargo-binstall -y zoxide@${ZOXIDE_VERSION} rumdl@${RUMDL_VERSION}

CMD ["sh", "-c", "exec sleep infinity"]
