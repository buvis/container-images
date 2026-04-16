FROM ghcr.io/buvis/koolna-base:latest@sha256:aeae170adb8d952d9ba0f4bb016962362b7337752aaec0c7ec5f5a5fdbf0a2ee

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
