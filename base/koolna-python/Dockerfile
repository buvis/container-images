FROM ghcr.io/buvis/koolna-base:latest@sha256:b93b1f2c1f4e3165b9da43d42a2964fc7060dda102bbc86d63a07ec692a96a61

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
