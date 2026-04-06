FROM ghcr.io/buvis/koolna-base:latest@sha256:a67dae2115c823d9b4dec236e3245a54cd1d8e6b6ca9c7eef8bf493bb9a9bbe5

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
