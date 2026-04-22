FROM ghcr.io/buvis/koolna-base:latest@sha256:6132235cd35b6cb52710dad1441472a0c6656812a1019ae1772f7d7a5d16e741

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
