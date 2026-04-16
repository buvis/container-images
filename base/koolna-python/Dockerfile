FROM ghcr.io/buvis/koolna-base:latest@sha256:d428682f5407f14f53f2b8f3acf1930e4b7882e37ac8a2309da790e046d6c829

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
