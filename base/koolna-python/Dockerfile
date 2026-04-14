FROM ghcr.io/buvis/koolna-base:latest@sha256:8803e6d006abc3632fa4c6e6f1a405235ffd069f1a4e8941d2176cec88bb3b33

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
