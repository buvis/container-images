FROM ghcr.io/buvis/koolna-base:latest@sha256:5b41aaccf5f14c104098aa2589c1d8576d7aa40e33171dda339342e175b7cf85

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
