FROM ghcr.io/buvis/koolna-base:latest@sha256:06298e437de536f2e61d1d76f5217cc87f5d2ea572e1ef31b0ca7b388a8077eb

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
