FROM ghcr.io/buvis/koolna-base:latest@sha256:be86b9e6b6bd177efc03f1cd1fd12b498f8babba0a8c5071b0b2163241d4798c

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
