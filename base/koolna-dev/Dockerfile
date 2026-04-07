FROM ghcr.io/buvis/koolna-base:latest@sha256:c3db8d1920abb5ef48ede1a65897cba4ffa56f55601fe8988ed1b5f694fd980d

ARG USERNAME=bob

# --- Rust apt dependencies (build-essential, pkg-config) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

USER $USERNAME

ENV HOME=/home/$USERNAME
ENV PATH="$HOME/.cargo/bin:$PATH"
ENV MISE_NODE_DEFAULT_PACKAGES_FILE="$HOME/.default-npm-packages"

# --- Node.js GPG keys ---
RUN gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 \
  || gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4

# --- Config files ---
COPY --chown=${USERNAME}:${USERNAME} assets/config/.default-npm-packages /home/$USERNAME/.default-npm-packages
COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

# --- Install all runtimes via mise ---
RUN bash -c 'eval "$(mise activate bash)" && mise install'

# --- Rust cargo tools (cargo-binstall + zoxide, rumdl) ---
ARG CARGO_BINSTALL_VERSION=v1.17.9
ARG CARGO_BINSTALL_SHA256=c2e963fbab3bdd8653b59c28d349bf85740cf4998e5e398d250dcd2884cd667d
RUN curl -fsSL "https://raw.githubusercontent.com/cargo-bins/cargo-binstall/${CARGO_BINSTALL_VERSION}/install-from-binstall-release.sh" -o /tmp/install-binstall.sh \
  && echo "${CARGO_BINSTALL_SHA256}  /tmp/install-binstall.sh" | sha256sum -c - \
  && bash /tmp/install-binstall.sh \
  && rm /tmp/install-binstall.sh

RUN $HOME/.cargo/bin/cargo-binstall -y zoxide rumdl

CMD ["sh", "-c", "exec sleep infinity"]
