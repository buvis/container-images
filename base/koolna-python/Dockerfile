FROM ghcr.io/buvis/koolna-base:latest@sha256:d79d44738c29a07b00e6d4861de3c8650f050e3221ae4d6f49f11029cd3842d2

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
