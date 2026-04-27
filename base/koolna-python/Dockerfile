FROM ghcr.io/buvis/koolna-base:latest@sha256:11e010922d1907c24689138cd3956305a78aa8a72cdf8ed51e4cf8fd540a156c

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
