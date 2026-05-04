FROM ghcr.io/buvis/koolna-base:latest@sha256:bd5da23ba8f85402c59223732771696ac14fb55a73f3535b983efed0e71c2c5a

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
