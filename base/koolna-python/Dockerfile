FROM ghcr.io/buvis/koolna-base:latest@sha256:315d75400eb8f370ad1b3386f8eacb717ba0aafa2270d449fd7bbb77b8555e34

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
