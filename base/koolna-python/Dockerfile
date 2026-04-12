FROM ghcr.io/buvis/koolna-base:latest@sha256:1faa1ccd7f6720b49c0fa53765610dab64284b79ad81571eb018f7f9b2e797fa

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
