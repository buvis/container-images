FROM ghcr.io/buvis/koolna-base:latest@sha256:ce34586fa72b1e9552313a6883c9b8d2f9078b0f364427aff0b11eb726701946

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
