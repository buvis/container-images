FROM ghcr.io/buvis/koolna-base:latest@sha256:c3db8d1920abb5ef48ede1a65897cba4ffa56f55601fe8988ed1b5f694fd980d

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

# renovate: datasource=github-releases depName=cargo-bins/cargo-binstall
ARG CARGO_BINSTALL_VERSION=v1.17.9
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
