FROM ghcr.io/buvis/koolna-base:latest@sha256:c3db8d1920abb5ef48ede1a65897cba4ffa56f55601fe8988ed1b5f694fd980d

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
