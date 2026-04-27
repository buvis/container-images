FROM ghcr.io/buvis/koolna-base:latest@sha256:11e010922d1907c24689138cd3956305a78aa8a72cdf8ed51e4cf8fd540a156c

ARG USERNAME=bob

ENV HOME=/home/$USERNAME
USER $USERNAME

# Import Node.js release signing keys for GPG verification (fallback keyserver for CI reliability)
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  || gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

# renovate: datasource=npm depName=tree-sitter-cli
ARG TREE_SITTER_CLI_VERSION=0.26.8
RUN bash -c 'eval "$(mise activate bash)" && npm install -g tree-sitter-cli@${TREE_SITTER_CLI_VERSION}'

CMD ["sh", "-c", "exec sleep infinity"]
