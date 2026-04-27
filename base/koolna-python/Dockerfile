FROM ghcr.io/buvis/koolna-base:latest@sha256:509ef05ba5b6c7465a3c971c196e21aa7d3933d72bed156bc1a43a51f12e161f

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
